# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import inspect
import sys
import traceback
import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ipywidgets import Widget, register, widget_serialization
from traitlets import Container, Dict, Instance, Set, Unicode

import ipylab._frontend as _fe
from ipylab.hasapp import HasApp
from ipylab.hookspecs import pm

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

if TYPE_CHECKING:
    import types
    from collections.abc import Iterable
    from typing import ClassVar

    from ipylab.luminowidget_connection import LuminoWidgetConnection


__all__ = ["AsyncWidgetBase", "WidgetBase", "register", "pack", "Widget"]


def pack(obj: Widget | LuminoWidgetConnection | Any):
    """Return serialized obj if it is a Widget otherwise return it unchanged."""
    from ipylab.luminowidget_connection import LuminoWidgetConnection

    if isinstance(obj, LuminoWidgetConnection):
        return obj.id
    if isinstance(obj, Widget):
        return widget_serialization["to_json"](obj, None)
    return obj


def pack_code(code: str | types.ModuleType | Callable) -> str:
    """Convert code to a string suitable to run in a kernel."""
    if not isinstance(code, str):
        code = inspect.getsource(code)
    return code


class TransformMode(StrEnum):
    """The transformation to apply to the result of frontend operations prior to sending.

    - done: [default] A string '--DONE--'
    - raw: No conversion. Note: data is serialized when sending, some objects shouldn't be serialized.
    - string: Result is converted to a string.
    - attribute: A dotted attribute of the returned object is returned. ['path']='dotted.path.name'
    - function: Use a function to calculate the return value. ['code'] = 'function...'

    `attribute`
    ---------
    ```
    transform = {
        mode: "attribute",
        parts: ["dotted.attribute.name", ...],  # default transform is 'raw'
    }
    ```

    #### To specify a separate transform per part:

    ```
    transform = {
    mode: 'attribute',
    parts:  [{'path':'model', 'transform':...},, ...]
    }
    ```

    `function`
    --------
    JS code defining a function and the data to return.

    ```
    transform = {
        "mode": "function",
        "code": "function (obj) { return obj.id; }",
    }"""

    raw = "raw"
    done = "done"
    attribute = "attribute"
    function = "function"
    connection = "connection"


class JavascriptType(StrEnum):
    string = "string"
    number = "number"
    boolean = "boolean"
    object = "object"
    function = "function"


CallbackType = Callable[[dict[str, Any], Any], Any]
TransformType = TransformMode | dict[str, str]


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
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _comm = None
    add_traits = None  # type: ignore # Don't support the method HasTraits.add_traits as it creates a new type that isn't a subclass of its origin)


class AsyncWidgetBase(WidgetBase):
    """The base for all widgets that need async comms with the frontend model."""

    kernelId = Unicode(read_only=True).tag(sync=True)  # noqa: N815
    _async_widget_base_init_complete = False
    _ipylab_model_register: ClassVar[dict[str, Any]] = {}
    _singleton_register: ClassVar[dict[str, str]] = {}
    SINGLETON = False
    _ready_response = Instance(Response, ())
    _pending_operations: Dict[str, Response] = Dict()
    _tasks: Container[set[asyncio.Task]] = Set()
    _comm = None
    add_traits = None  # type: ignore # Don't support the method HasTraits.add_traits as it creates a new type that isn't a subclass of its origin)

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
        await self.wait_ready()
        self._check_closed()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def close(self):
        self._ipylab_model_register.pop(self.model_id, None)  # type: ignore
        for task in self._tasks:
            task.cancel()
        super().close()

    def _check_closed(self):
        if not self._repr_mimebundle_:
            msg = f"This widget is closed {self!r}"
            raise RuntimeError(msg)

    def _check_get_error(self, content: dict | None = None) -> IpylabFrontendError | None:
        if content is None:
            content = {}
        error = content.get("error")
        if error:
            operation = content.get("operation")
            if operation:
                msg = f'{self.__class__.__name__} operation "{operation}" failed with message "{error}"'
                if "cyclic" in error:
                    msg += (
                        "\nNote: A cyclic error may be due a return value that cannot be converted to JSON. "
                        "Try changing the transform (eg: transform=ipylab.TransformMode.done)."
                    )
                else:
                    msg += "\nNote: Additional information may be available in the browser console (`F12` in Firefox or  `Shift + CTRL + J` in Chrome)"
                return IpylabFrontendError(msg)

            return IpylabFrontendError(f'{self.__class__.__name__} failed with message "{error}"')
        return None

    async def wait_ready(self) -> None:
        await self._ready_response.wait()

    def send(self, content, buffers=None):
        try:
            super().send(content, buffers)
        except Exception as error:
            pm.hook.on_frontend_error(obj=self, error=error, content=content, buffers=buffers)

    async def _send_receive(self, content: dict, callback: CallbackType | None):
        async with self:
            self._pending_operations[content["ipylab_BE"]] = response = Response()
            self.send(content)
            try:
                return await self._wait_response_check_error(response, content, callback)
            except asyncio.CancelledError:
                if not self.comm:
                    msg = f"This widget is closed {self!r}"
                    raise asyncio.CancelledError(msg) from None
                raise

    async def _wait_response_check_error(self, response: Response, content: dict, callback: CallbackType | None) -> Any:
        payload = await response.wait()
        if callback:
            payload = callback(content, payload)
            if asyncio.iscoroutine(payload):
                payload = await payload
        if content["transform"] is TransformMode.connection:
            from ipylab.luminowidget_connection import LuminoWidgetConnection

            return LuminoWidgetConnection(id=payload)
        return payload

    def _on_frontend_msg(self, _, content: dict, buffers: list):
        error = self._check_get_error(content)
        if error:
            pm.hook.on_frontend_error(obj=self, error=error, content=content, buffers=buffers)
        if operation := content.get("operation"):
            ipylab_backend = content.get("ipylab_BE", "")
            payload = content.get("payload", {})
            if ipylab_backend:
                self._pending_operations.pop(ipylab_backend).set(payload, error)
            if "ipylab_FE" in content:
                task = asyncio.create_task(
                    self._handle_frontend_operation(content["ipylab_FE"], operation, payload, buffers)
                )
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        elif "init" in content:
            self._ready_response.set(content)
        elif "closed" in content:
            self.close()

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
        """Overload this function as required.
        or if there is a buffer can return a dict {"payload":dict, "buffers":[]}
        """
        pm.hook.unhandled_frontend_operation_message(obj=self, operation=operation)

    # TODO: add overloads for the transform type
    def schedule_operation(
        self,
        operation: str,
        *,
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
        **kwgs,
    ) -> asyncio.Task:
        """

        operation: str
            Name corresponding to operation in JS frontend.

        callback: callable | coroutine function.
            A callback to do additional processing on the response prior to returning a result.
            The callback is passed (response, content).
        transform : TransformMode | dict
            see ipylab.TransformMode
        note: If there is a name clash with the operation, use kwgs={}
        toLuminoWidget: Iterable[str] | None
            Items in kwgs that should be converted to a Lumino widget
            Each string should correspond to the dotted path/index in kwgs that has
            the packed (json version of the widget or id of a lumino widget)
            Examples:
            --------
                kwgs = {'widget': 'IPY_MODEL_...', 'options':{'ref':'id...'}}
                toLuminoWidget = ['widget', 'options.ref']

                kwgs = {'args':['id...',1,2,'id...']}
                toLuminoWidget = ['args.0', 'args.3']

        **kwgs: Keyword arguments for the frontend operation.
        """
        # validation
        self._check_closed()
        if not operation or not isinstance(operation, str):
            msg = f"Invalid {operation=}"
            raise ValueError(msg)
        ipylab_BE = str(uuid.uuid4())  # noqa: N806
        content = {"ipylab_BE": ipylab_BE, "operation": operation, "kwgs": kwgs, "transform": TransformMode(transform)}
        if toLuminoWidget:
            content["toLuminoWidget"] = list(map(str, toLuminoWidget))
        if callback and not callable(callback):
            msg = f"callback is not callable {callback!r}"
            raise TypeError(msg)
        task = asyncio.create_task(self._send_receive(content, callback))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def execute_method(
        self,
        method: str,
        *args,
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
    ) -> asyncio.Task:
        """Call a method on the corresponding frontend object.

        method: 'dotted.access.to.the.method' relative to the Frontend instance.

        *args
        `args` are passed in order so must correspond with the order in the JS method.
        Specifying arguments by name is not currently support.

        example:
        ```
        app.execute_method(widget=app.current_widget_id, method="close")
        ```
        """

        # This operation is sent to the frontend function _fe_execute in 'ipylab/src/widgets/ipylab.ts'

        # validation
        if callback is not None and not callable(callback):
            msg = "callback must be a callable or None"
            raise TypeError(msg)
        return self.schedule_operation(
            operation="FE_execute",
            FE_execute={
                "mode": "execute_method",
                "kwgs": {"method": method},
            },
            transform=transform,
            callback=callback,
            args=args,
            toLuminoWidget=toLuminoWidget,
        )

    def get_attribute(
        self, path: str, *, callback: CallbackType | None = None, transform: TransformType = TransformMode.raw
    ):
        """A serialized version of the attribute relative to this object."""
        return self.execute_method("getAttribute", path, callback=callback, transform=transform)

    def list_methods(self, path: str = "", depth=2, skip_hidden=True) -> asyncio.Task[list[str]]:  # noqa: FBT002
        """Get a list of methods belonging to the object 'path' of the Frontend instance.
        depth: The depth in the object inheritance to search for methods.
        """

        def callback(content: dict, payload: list):  # noqa: ARG001
            if skip_hidden:
                return [n for n in payload if not n.startswith("_")]
            return payload

        return self.list_attributes(path, "function", depth, how="names", callback=callback)  # type: ignore

    def list_attributes(
        self,
        path: str = "",
        type: JavascriptType = JavascriptType.function,  # noqa: A002
        depth=2,
        *,
        how="group",
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
    ) -> asyncio.Task[dict | list]:
        """Get a mapping of attributes of the object at 'path' of the Frontend instance.

        depth: The depth in the object inheritance to search for attributes.
        how: ['names', 'group', 'raw'] (ignored if callback provided)
        """

        def callback_(content: dict, payload: Any):
            if how == "names":
                payload = [row["name"] for row in payload]
            elif how == "group":
                groups = {}
                for item in payload:
                    st = groups.get(item["type"], [])
                    st.append(item["name"])
                    groups[item["type"]] = st
                payload = groups
            if callback:
                payload = callback(content, payload)
            return payload

        return self.execute_method("listAttributes", path, type, depth, callback=callback_, transform=transform)

    def execute_command(self, command_id: str, transform: TransformType = TransformMode.done, **args) -> asyncio.Task:
        """Execute command_id.

        `args` correspond to `args` in JupyterLab.

        Finding what the `args` are remains an outstanding issue in JupyterLab.

        see: https://github.com/jtpio/ipylab/issues/128#issuecomment-1683097383 for hints
        about how args can be found.
        """
        return self.execute_method("app.commands.execute", command_id, args, transform=transform)
