# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Callable, Coroutine

from ipywidgets import Widget, register, widget_serialization
from traitlets import Dict, Instance, Set, Unicode, Bool
from ipylab._plugin_manger import pm

import ipylab._frontend as _fe
from ipylab._plugin_manger import pm
from IPython.core.getipython import get_ipython

__all__ = ["AsyncWidgetBase", "WidgetBase", "register", "pack", "Widget"]

# Currently only checks for an IPython kernel. A better way of getting the kernel_id would be useful.
ip = get_ipython()
KERNEL_ID = (
    ip.kernel.config["IPKernelApp"]["connection_file"].split("kernel-", 1)[1].removesuffix(".json")
    if ip
    else "NO KERNEL"
)


def pack(obj):
    if isinstance(obj, Widget):
        obj = widget_serialization["to_json"](obj, None)
    return obj


class Response(asyncio.Event):
    def set(self, payload, error: Exception | None = None) -> None:
        if self._value:
            raise RuntimeError("Already set!")
        self.payload = payload
        self.error = error
        super().set()

    async def wait(self) -> Any:
        """Wait for a message and return the response."""
        await super().wait()
        if self.error:
            raise self.error
        return self.payload


class IpylabFrontendError(IOError):
    pass


class WidgetBase(Widget):
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _comm = None


class AsyncWidgetBase(WidgetBase):
    """The base for all widgets that need async comms with the model."""

    kernel_id = Unicode(KERNEL_ID, read_only=True).tag(sync=True)
    _ipylab_model_register: dict[str, "AsyncWidgetBase"] = {}
    _singleton_register: dict[type, str] = {}
    SINGLETON = False
    _ready_response = Instance(Response, ())
    _model_id = None
    _pending_operations: dict[str, Response] = Dict()
    _tasks: set[asyncio.Task] = Set()
    _comm = None
    closed = Bool(read_only=True).tag(sync=True)
    OPERATION_DONE = "--DONE--"

    def __repr__(self):
        return f"<{self.__class__.__name__} at {id(self)}>"

    def __new__(cls, *, model_id=None, **kwgs):
        if not model_id and cls.SINGLETON:
            model_id = cls._singleton_register.get(cls.__name__)
        if model_id and model_id in cls._ipylab_model_register:
            return cls._ipylab_model_register[model_id]
        inst = super().__new__(cls, model_id=model_id, **kwgs)
        return inst

    def __init__(self, *, model_id=None, **kwgs):
        if self._model_id:
            return
        if not self.kernel_id:
            raise RuntimeError(
                f"{self.__class__.__name__} requries a running kernel."
                "kernel_id is not set meaning that a kernel is not running."
            )
        super().__init__(model_id=model_id, **kwgs)
        self._ipylab_model_register[self.model_id] = self
        if self.SINGLETON:
            self._singleton_register[self.__class__.__name__] = self.model_id
        self.on_msg(self._on_frontend_msg)

    async def __aenter__(self):
        if not self._ready_response.is_set():
            await self.wait_ready()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def open(self) -> None:
        self._check_closed()
        super().open()

    def close(self):
        self._ipylab_model_register.pop(self._model_id, None)
        for task in self._tasks:
            task.cancel()
        super().close()
        self.set_trait("closed", True)

    def _check_closed(self):
        if self.closed:
            raise RuntimeError(f"This object is closed {self}")

    def _check_get_error(self, content={}) -> IpylabFrontendError | None:
        error = content.get("error")
        if error:
            if operation := content.get("operation"):
                return IpylabFrontendError(
                    f"{self.__class__.__name__} operation '{operation}' failed with message \"{error}\""
                )
            return IpylabFrontendError(f'{self.__class__.__name__} failed with message "{error}"')
        else:
            return None

    async def wait_ready(self) -> None:
        if not self._ready_response.is_set():
            self.log.info(f"Connecting to frontend {self._model_name}")
            await self._ready_response.wait()
            self.log.info(f"Connected to frontend {self._model_name}")

    def send(self, content, buffers=None):
        try:
            super().send(content, buffers)
        except Exception as error:
            pm.hook.on_send_error(self, error, content, buffers)

    async def _send_receive(self, content: dict, callback: Callable):
        async with self:
            self._pending_operations[content["ipylab_BE"]] = response = Response()
            self.send(content)
            return await self._wait_response_check_error(response, content, callback)

    async def _wait_response_check_error(
        self, response: Response, content: dict, callback: Callable
    ) -> Any:
        payload = await response.wait()
        if callback:
            payload = callback(content, payload)
            if asyncio.iscoroutine(payload):
                payload = await payload
        return payload

    def _on_frontend_msg(self, _, content: dict, buffers: list):
        error = self._check_get_error(content)
        if operation := content.get("operation"):
            ipylab_BE = content.get("ipylab_BE", "")
            payload = content.get("payload", {})
            if ipylab_BE:
                if payload == self.OPERATION_DONE:
                    payload = None
                self._pending_operations.pop(ipylab_BE).set(payload, error)
            elif error:
                pm.hook.on_frontend_error(obj=self, error=self.error, content=content)
            ipylab_FE = content.get("ipylab_FE", "")
            if ipylab_FE:
                task = asyncio.create_task(
                    self._handle_frontend_operation(ipylab_FE, operation, payload, buffers)
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        elif init_message := content.get("init"):
            self._ready_response.set(content)
            print(init_message)

    def add_traits(self, **traits):
        raise NotImplementedError("Using this method is a bad idea! Make a subclass instead.")

    async def _handle_frontend_operation(
        self, ipylab_FE: str, operation: str, payload: dict, buffers: list
    ):
        """Handle operation requests from the frontend and reply with a result."""
        content = {"ipylab_FE": ipylab_FE}
        buffers = []
        try:
            payload_ = self._do_operation_for_frontend(operation, payload, buffers)
            if asyncio.iscoroutine(payload_):
                payload_ = await payload_
            if payload_ is None:
                pm.hook.unhandled_frontend_operation_message(self, operation)
                raise ValueError(f"{operation=}")
            if isinstance(payload_, dict) and "buffers" in payload_:
                buffers = payload_["buffers"]
                payload_ = payload_["payload"]
            content["payload"] = payload_
        except asyncio.CancelledError:
            content["error"] = "Cancelled"
        except Exception as e:
            content["error"] = str(e)
            pm.hook.on_frontend_operation_error(self, error=e, content=payload)
        finally:
            self.send(content, buffers)

    def _do_operation_for_frontend(self, operation: str, payload: dict, buffers):
        """Overload this function as required.

        Should return something that isn't `None` that is json serializable.
        or if there is a buffer can return a dict {"payload":dict, "buffers":[]}
        """

    def schedule_operation(
        self, operation: str, *, callback: Callable[[any, any], None | Coroutine] = None, **kwgs
    ) -> asyncio.Task:
        """
        operation: str
            Name corresponding to operation in JS frontend.
        callback: callable | coroutine function.
            A callback to do additional processing on the response prior to returning a result.
            The callback is passed (response, content).
        kwgs: Named arguments passed to the frontend operation.

        """
        self._check_closed()
        if not operation or not isinstance(operation, str):
            raise ValueError(f"Invalid {operation=}")
        ipylab_BE = str(uuid.uuid4())
        content = {"ipylab_BE": ipylab_BE, "operation": operation, "kwgs": kwgs}
        if callback and not callable(callback):
            raise TypeError(f"callback is not callable {type(callback)=}")
        task = asyncio.create_task(self._send_receive(content, callback))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def execute_method(
        self,
        method: str,
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        **kwgs,
    ) -> asyncio.Task:
        "Call a method on the corresponding frontend object."
        return self.schedule_operation(
            operation="FE_execute",
            FE_execute={
                "mode": "execute_method",
                "kwgs": {"method": method},
            },
            callback=callback,
            **kwgs,
        )
