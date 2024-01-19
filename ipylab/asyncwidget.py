# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Callable, Never

from ipywidgets import DOMWidget, Widget, register, widget_serialization
from traitlets import Dict, Instance, Set, Unicode

import ipylab._frontend as _fe

__all__ = ["AsyncWidgetBase", "WidgetBase", "register", "widget_serialization", "pack", "Widget"]


def pack(obj):
    if isinstance(obj, Widget):
        obj = widget_serialization["to_json"](obj, None)
    return obj


class Response(asyncio.Event):
    def set(self, payload, error=None) -> None:
        if self._value:
            raise RuntimeError("Already set!")
        self.payload = payload
        self.error = error
        super().set()

    async def wait(self) -> tuple[Any, str | None]:
        """Wait for a message and return the response."""
        await super().wait()
        return self.payload, self.error


class IpylabFrontendError(IOError):
    pass


class WidgetBase(DOMWidget):
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)


class AsyncWidgetBase(WidgetBase):
    """The base for all widgets that need async comms with the model."""

    _view_module = Unicode("", read_only=True).tag(sync=True)
    _view_module_version = Unicode("", read_only=True).tag(sync=True)
    _ipylab_model_register: dict[str, "AsyncWidgetBase"] = {}
    _singleton_register: dict[type, str] = {}
    SINGLETON = False
    _ready_response = Instance(Response, ())
    _model_id = None
    _pending_events: dict[str, Response] = Dict()
    _tasks = Set()

    def __repr__(self):
        return f"<{self.__class__.__name__} at {id(self)}>"

    def __new__(cls, model_id=None, **kwargs):
        if not model_id and cls.SINGLETON:
            model_id = cls._singleton_register.get(cls.__name__)
        if model_id and model_id in cls._ipylab_model_register:
            return cls._ipylab_model_register[model_id]
        inst = super().__new__(cls, model_id=model_id, **kwargs)
        return inst

    def __init__(self, model_id=None, **kwargs):
        if self._model_id:
            return
        super().__init__(model_id=model_id, **kwargs)
        self._ipylab_model_register[self.model_id] = self
        if self.SINGLETON:
            self._singleton_register[self.__class__.__name__] = self.model_id
        self.on_msg(self._on_frontend_msg)

    async def __aenter__(self):
        if not self._ready_response.is_set():
            await self.wait_ready()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def _to_error(self, error: str) -> IpylabFrontendError | None:
        if error:
            return IpylabFrontendError(error)
        else:
            return None

    async def wait_ready(self) -> None:
        if not self._ready_response.is_set():
            self.log.info(f"Connecting to frontend {self._model_name}")
            await self._ready_response.wait()
            self.log.info(f"Connected to frontend {self._model_name}")

    def close(self):
        self._ipylab_model_register.pop(self._model_id, None)
        super().close()

    def schedule_operation(self, operation: str, **kwgs) -> asyncio.Task:
        if not operation or not isinstance(operation, str):
            raise ValueError(f"Invalid {operation=}")
        ipylab_ID = str(uuid.uuid4())
        msg = {"ipylab_ID": ipylab_ID, "operation": operation, "kwgs": kwgs}
        task = asyncio.create_task(self._send_recieve(msg, self._wait_response_check_error))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _send_recieve(self, msg: dict, parser: None | Callable[[Response, dict]]):
        async with self:
            self._pending_events[msg["ipylab_ID"]] = response = Response()
            self.send(msg)
            if parser:
                return await parser(response, msg)
            else:
                return response

    async def _wait_response_check_error(self, response: Response, msg: dict) -> Any:
        payload, error = await response.wait()
        if error:
            self.error_handler(self, error, msg)
        return payload

    @staticmethod
    def error_handler(obj: AsyncWidgetBase, error_message: str, msg: dict) -> Never:
        "Can be overridden to add a logger or other special handling."
        raise IpylabFrontendError(
            f"{obj.__class__.__name__} operation '{msg.get('operation')}' failed with message '{error_message}'"
        )

    def _on_frontend_msg(self, _, content: dict, buffers: list):
        error = self._to_error(content.get("error"))
        if event := content.get("event"):
            ipylab_ID = content.get("ipylab_ID", "")
            payload = content.get("payload", {})
            if ipylab_ID:
                self._pending_events.pop(ipylab_ID).set(payload, error)
            else:
                self._on_event(event, payload, buffers, error)
        elif init_message := content.get("init"):
            self._ready_response.set(content)
            print(init_message)

    def add_traits(self, **traits):
        raise NotImplementedError("Using this method is a bad idea! Make a subclass instead.")

    def _on_event(self, event: str, payload: dict, buffers, error: IpylabFrontendError | None):
        # To overload.
        if error:
            raise error
