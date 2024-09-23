# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import inspect
import json
import traceback
import uuid
from typing import TYPE_CHECKING, Any, TypeVar

from ipywidgets import Widget, register, widget_serialization
from traitlets import Container, Dict, HasTraits, Instance, Set, Unicode

import ipylab._frontend as _fe
from ipylab.common import JavascriptType, Transform, TransformType
from ipylab.hasapp import HasApp
from ipylab.hookspecs import pm

if TYPE_CHECKING:
    import logging
    from asyncio import Task
    from collections.abc import Awaitable, Coroutine, Iterable
    from typing import ClassVar, Literal, overload

    from ipylab.commands import CommandConnection


__all__ = ["AsyncWidgetBase", "WidgetBase", "register", "pack", "Widget"]

T = TypeVar("T")


if TYPE_CHECKING:

    @overload
    def pack(obj: Widget) -> str: ...
    @overload
    def pack(obj: T) -> T: ...


def pack(obj):
    """Return serialized obj if it is a Widget otherwise return it unchanged."""

    if isinstance(obj, Widget):
        return widget_serialization["to_json"](obj, None)
    return obj


def pack_code(code: str | inspect._SourceObjectType) -> str:
    """Convert code to a string suitable to run in a kernel."""
    if not isinstance(code, str):
        code = inspect.getsource(code)
    return code


class Response(asyncio.Event):
    def set(self, payload, error: Exception | None = None) -> None:
        if getattr(self, "_value", False):
            msg = "Already set!"
            raise RuntimeError(msg)
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


class WidgetBase(Widget, HasApp):
    _model_name = None  # Ensure this gets overloaded
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _comm = None
    add_traits = None  # type: ignore # Don't support the method HasTraits.add_traits as it creates a new type that isn't a subclass of its origin)


@register
class AsyncWidgetBase(WidgetBase):
    """The base for all widgets that need async comms with the frontend model."""

    _model_name = Unicode("IpylabModel", help="Name of the model.", read_only=True).tag(sync=True)
    _basename = Unicode(allow_none=True).tag(sync=True)
    kernelId = Unicode(read_only=True).tag(sync=True)  # noqa: N815
    _async_widget_base_init_complete = False
    _ipylab_model_register: ClassVar[dict[str, Any]] = {}
    _singleton_register: ClassVar[dict[str, str]] = {}
    SINGLETON = False
    _ready_event = Instance(asyncio.Event, ())
    _pending_operations: Dict[str, Response] = Dict()
    _tasks: Container[set[asyncio.Task]] = Set()
    _comm = None
    add_traits = None  # type: ignore # Don't support the method HasTraits.add_traits as it creates a new type that isn't a subclass of its origin)
    if TYPE_CHECKING:
        log: logging.Logger

    def __new__(cls, *, model_id=None, **kwgs):
        if not model_id and cls.SINGLETON:
            model_id = cls._singleton_register.get(cls.__name__)
        if model_id and model_id in cls._ipylab_model_register:
            return cls._ipylab_model_register[model_id]
        return super().__new__(cls, model_id=model_id, **kwgs)

    def __init__(self, *, model_id=None, **kwgs):
        if self._async_widget_base_init_complete:
            return
        super().__init__(model_id=model_id, **kwgs)
        assert self.model_id  # noqa: S101
        self._ipylab_model_register[self.model_id] = self
        if self.SINGLETON:
            self._singleton_register[self.__class__.__name__] = self.model_id
        self.on_msg(self._on_frontend_msg)
        self._async_widget_base_init_complete = True

    async def __aenter__(self):
        await self._ready_event.wait()
        self._check_closed()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def close(self):
        "Permanently close the widget."
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        if self._repr_mimebundle_ and self._model_id:
            self._ipylab_model_register.pop(self._model_id, None)
            super().close()

    def _check_closed(self):
        if not self._repr_mimebundle_:
            msg = f"This widget is closed {self!r}"
            raise RuntimeError(msg)

    def to_task(self, coro: Coroutine[None, None, T]) -> Task[T]:
        """Run the coro in a task."""

        self._check_closed()
        task = asyncio.create_task(self._wrap_coro(coro))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _wrap_coro(self, coro: Coroutine[None, None, T]) -> T:
        try:
            async with self:
                return await coro
        except asyncio.CancelledError:
            raise
        except Exception as e:
            try:
                pm.hook.on_task_error(obj=self, error=e)
                msg = f"Exception for  {type(self)}"
                self.log.exception(msg)
            finally:
                raise e

    def _check_get_error(self, content: dict) -> IpylabFrontendError | None:
        if "error" in content:
            error = content["error"]
            operation = content.get("operation")
            if operation:
                msg = f'{self.__class__.__name__} operation "{operation}" failed with message "{error}"'
                if "cyclic" in error:
                    msg += (
                        "\nNote: A cyclic error may be due a return value that cannot be converted to JSON. "
                        "Try changing the transform (eg: transform=ipylab.Transform.done)."
                    )
                else:
                    msg += "\nNote: Additional information may be available in the browser console (press `F12`)"
                return IpylabFrontendError(msg)

            return IpylabFrontendError(f'{self.__class__.__name__} failed with message "{error}"')
        return None

    async def _add_to_tuple_trait(self, name: str, item: Awaitable[T] | T) -> T:
        """Add the item to the tuple and observe its comm."""
        if inspect.isawaitable(item):
            value: T = await item
        else:
            value: T = item
        items = getattr(self, name)
        if isinstance(value, HasTraits) and value not in items:
            value.observe(lambda _: self.set_trait(name, tuple(i for i in getattr(self, name) if i.comm)), "comm")
            self.set_trait(name, (*items, value))
        return value

    def send(self, content, buffers=None):
        try:
            super().send(content, buffers)
        except Exception as error:
            pm.hook.on_frontend_error(obj=self, error=error, content=content, buffers=buffers)

    async def _send_receive(self, content: dict):
        async with self:
            self._pending_operations[content["ipylab_BE"]] = response = Response()
            self.send(content)
            try:
                return await self._wait_response_check_error(response, content)
            except asyncio.CancelledError:
                if not self.comm:
                    msg = f"This widget is closed {self!r}"
                    raise asyncio.CancelledError(msg) from None
                raise

    async def _wait_response_check_error(self, response: Response, content: dict) -> Any:
        payload = await response.wait()
        return Transform.transform_payload(content["transform"], payload)

    def _on_frontend_msg(self, _, content: dict, buffers: list):
        error = self._check_get_error(content)
        if error:
            pm.hook.on_frontend_error(obj=self, error=error, content=content, buffers=buffers)
        if operation := content.get("operation"):
            ipylab_autostart = content.get("ipylab_BE", "")
            payload = content.get("payload", {})
            if ipylab_autostart:
                self._pending_operations.pop(ipylab_autostart).set(payload, error)
            if "ipylab_FE" in content:
                self.to_task(self._handle_frontend_operation(content["ipylab_FE"], operation, payload, buffers))
        elif "init" in content:
            self._ready_event.set()
            self.on_frontend_init(content)
        elif "closed" in content:
            self.close()

    def on_frontend_init(self, content: dict):
        """Called when the frontend is initialized.

        This will occur on initial connection and whenever the model is restored from the kernel."""

    async def _handle_frontend_operation(self, ipylab_FE: str, operation: str, payload: dict, buffers: list):
        """Handle operation requests from the frontend and reply with a result."""
        content: dict[str, Any] = {"ipylab_FE": ipylab_FE}
        buffers = []
        try:
            result = await self._do_operation_for_frontend(operation, payload, buffers)
            if isinstance(result, dict) and "buffers" in result:
                buffers = result["buffers"]
                result = result["payload"]
            content["payload"] = result
        except asyncio.CancelledError:
            content["error"] = "Cancelled"
        except Exception as e:
            content["error"] = {
                "repr": repr(e).replace("'", '"'),
                "traceback": traceback.format_tb(e.__traceback__),
            }
            pm.hook.on_frontend_error(obj=self, error=e, content=content, buffers=buffers)
        finally:
            try:
                self.send(content, buffers)
            except ValueError as e:
                content.pop("payload", None)
                content["error"] = {
                    "repr": repr(e).replace("'", '"'),
                    "traceback": traceback.format_tb(e.__traceback__),
                }
                self.send(content, buffers)
                pm.hook.on_frontend_error(obj=self, error=e, content=content, buffers=buffers)

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list):  # noqa: ARG002
        """Overload this function as required."""
        pm.hook.unhandled_frontend_operation_message(obj=self, operation=operation)

    def schedule_operation(
        self,
        operation: str,
        *,
        transform: TransformType = Transform.raw,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
        **kwgs,
    ):
        """Create a new task requesting an operation to be performed in the frontend.

        operation: str
            Name corresponding to operation in JS frontend.

        transform : Transform | dict
            The transform to apply to the result of the operation.
            see: ipylab.Transform

        toLuminoWidget: Iterable[str] | None
            A list of item name mappings to convert to a Lumino widget in the frontend.
            Each string should correspond to the dotted path/index in kwgs that has
            the packed (json version of the widget or id of a lumino widget)

        toObject:  Iterable[str] | None
            A list of item name mappings in the .

            ```
            Examples:
            --------

            ```python
            kwgs = {"widget": "IPY_MODEL_<UUID>", "options": {"ref": "IPY_MODEL_<UUID>"}}
            toLuminoWidget = ["widget", "options.ref"]

            kwgs = {
                "args": [
                    "IPY_MODEL_<UUID>",
                    1,
                    "dotted.attribute.name",
                    "IPY_MODEL_<UUID>.value",
                ]
            }
            toLuminoWidget = ["args.0", "kwgs.options.ref"]
            toObject = ["args.2", "args.3"]"""
        # validation
        self._check_closed()
        if not operation or not isinstance(operation, str):
            msg = f"Invalid {operation=}"
            raise ValueError(msg)
        ipylab_BE = str(uuid.uuid4())  # noqa: N806
        content = {
            "ipylab_BE": ipylab_BE,
            "operation": operation,
            "kwgs": kwgs,
            "transform": Transform.validate(transform),
        }
        if toLuminoWidget:
            content["toLuminoWidget"] = list(map(str, toLuminoWidget))
        if toObject:
            content["toObject"] = list(map(str, toObject))

        return self.to_task(self._send_receive(content))

    def execute_command(
        self,
        command_id: str | CommandConnection,
        *,
        transform: TransformType = Transform.done,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
        **args,
    ):
        """Execute any command registered in Jupyterlab.

        `args` are passed to the command.

        see: https://github.com/jtpio/ipylab/issues/128#issuecomment-1683097383 for hints
        about what args can be used.
        """
        id_ = str(command_id)
        if id_ not in self.app.commands.all_commands:
            msg = f"Command with id='{id_}' is not registered!"
            raise ValueError(msg)
        return self.schedule_operation(
            "executeCommand",
            id=id_,
            args=args,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
            toObject=toObject,
        )

    def execute_method(
        self,
        path: str,
        *args,
        transform: TransformType = Transform.raw,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
        **kwgs,
    ):
        """Call a method relative to the `base` object in the Frontend.

        path: 'dotted.access.to.the.method' relative to base.

        *args
        `args` are passed in order so must correspond with the order in the JS method.
        Specifying arguments by name is not currently supported.

        **kwgs are only used for the transform.

        example:
        ```
        app.execute_method(widget=app.current_widget_id, method="close")
        ```
        """
        # This operation is sent to the frontend function _fe_execute in 'ipylab/src/widgets/ipylab.ts'
        return self.schedule_operation(
            operation="executeMethod",
            path=path,
            args=args,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
            toObject=toObject,
            **kwgs,
        )

    def get_property(self, path: str, *, transform: TransformType = Transform.raw, nullIfMissing=False):
        """Obtain a serialized version of the property of the `base` object in the frontend.

        path: 'dotted.access.to.the.method' relative to base.

        Tip: This method will await the property in the Frontend prior to returning the result
        where the property is an awaitable.
        """
        return self.schedule_operation("getProperty", path=path, nullIfMissing=nullIfMissing, transform=transform)

    def set_property(
        self,
        path: str,
        value,
        *,
        value_transform: TransformType = Transform.raw,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
        transform=Transform.done,
    ):
        """Set the property on the `path` of the `base` object in the Frontend.

        The value will be transformed according to `value_transform` & `value_transform_kwgs`
        as specified prior to setting the property.

        path: str
            "the.path.to.the.property" to be set.
        value: jsonable
            The value to set, or instructions for the transform to do in the Frontend.
        valueTransform: TransformType
            valueTransform is applied to the value prior to setting the property.
            It may be specified as a dict with the mapping: transform:TransformType.<value>
        toLuminoWidget: ['value'] | None
            Nested notation is also possible under `value`.
        toObject: ['value'] | None
            Nested notation is also possible under `value`.
        """
        return self.schedule_operation(
            "setProperty",
            path=path,
            value=pack(value),
            valueTransform=Transform.validate(value_transform),
            toLuminoWidget=toLuminoWidget,
            toObject=toObject,
            transform=transform,
        )

    def update_property(
        self,
        path: str,
        value: dict,
        *,
        value_transform: TransformType = Transform.raw,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
    ):
        """Update the value of the object at the path in the frontend.

        This is equivalent to `dict.update` in Python.

        path: str
            "the.path.to.the.property" to be set.
        toLuminoWidget: ['value'] | None
            Nested notation is also possible under `value`.
        toObject: ['value'] | None
            Nested notation is also possible under `value`.
        """

        return self.schedule_operation(
            "updateProperty",
            path=path,
            value=json.loads(json.dumps(value, default=pack)),
            transform=Transform.raw,
            valueTransform=Transform.validate(value_transform),
            toLuminoWidget=toLuminoWidget,
            toObject=toObject,
        )

    def list_properties(
        self,
        path: str = "",
        type: JavascriptType = JavascriptType.function,  # noqa: A002
        depth=3,
        *,
        how: Literal["names", "group", "raw"] = "group",
        transform: TransformType = Transform.raw,
        skip_hidden=True,
    ) -> Task[dict | list]:
        """Get a mapping of properties of the object at 'path' of the Frontend instance.

        depth: The depth in the object inheritance to search for properties.
            Searching deeper will reveal more lower level properties.
        how: ['names', 'group', 'raw']
        """
        task = self.schedule_operation("listProperties", path=path, type=type, depth=depth, transform=transform)

        async def list_properties():
            def filt(x: dict | str):
                if not skip_hidden:
                    return x
                if isinstance(x, dict):
                    return not x["name"].startswith("_")
                return not x.startswith("_")

            payload: list = await task  # type: ignore
            if how == "names":
                payload = [row["name"] for row in filter(filt, payload)]
            elif how == "group":
                groups = {}
                for item in filter(filt, payload):
                    st = groups.get(item["type"], [])
                    st.append(item["name"])
                    groups[item["type"]] = st
                return groups
            return list(filter(filt, payload))

        return self.to_task(list_properties())  # type: ignore

    def list_methods(self, path: str = "", *, depth=3, skip_hidden=True):
        """Get a list of methods belonging to the object 'path' of the Frontend instance.
        depth: The depth in the object inheritance to search for methods.
        """
        task = self.list_properties(path, JavascriptType.function, depth, how="names")

        async def list_methods():
            payload = (await task) or []
            if skip_hidden:
                return [n for n in payload if not n.startswith("_")]
            return payload

        return self.to_task(list_methods())
