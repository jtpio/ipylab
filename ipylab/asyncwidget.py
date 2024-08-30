# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import inspect
import traceback
import uuid
from typing import TYPE_CHECKING, Any

from ipywidgets import Widget, register, widget_serialization
from traitlets import Container, Dict, Instance, Set, Unicode

import ipylab._frontend as _fe
from ipylab._compat.enum import StrEnum
from ipylab.hasapp import HasApp
from ipylab.hookspecs import pm

if TYPE_CHECKING:
    import logging
    from asyncio import Task
    from collections.abc import Coroutine, Iterable
    from typing import ClassVar, Literal


__all__ = ["AsyncWidgetBase", "WidgetBase", "register", "pack", "Widget"]


def pack(obj: Widget | Any):
    """Return serialized obj if it is a Widget otherwise return it unchanged."""

    if isinstance(obj, Widget):
        return widget_serialization["to_json"](obj, None)
    return obj


def pack_code(code: str | inspect._SourceObjectType) -> str:
    """Convert code to a string suitable to run in a kernel."""
    if not isinstance(code, str):
        code = inspect.getsource(code)
    return code


class TransformMode(StrEnum):
    """The transformation to apply to the result of frontend operations prior to sending.

    - done: [default] A string '--DONE--'
    - raw: No conversion. Note: data is serialized when sending, some objects shouldn't be serialized.
    - attribute: A dotted attribute of the returned object is returned. ['path']='dotted.path.name'
    - function: Use a function to calculate the return value. ['code'] = 'function...'
    - connection: Return a connection to a disposable object in the frontend.
        By default the disposable will be closed when the kernel is shutdown.
        To leave the disposable open use the setting `onKernelLost=False` when creating the connection.

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

    The function must accept two args: obj, options.

    ```
    transform = {
        "transform": TransformMode.function,
        "code": "function (obj, options) { return obj.id; }",
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
    _model_name = None  # Ensure this gets overloaded
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _comm = None
    add_traits = None  # type: ignore # Don't support the method HasTraits.add_traits as it creates a new type that isn't a subclass of its origin)


class AsyncWidgetBase(WidgetBase):
    """The base for all widgets that need async comms with the frontend model."""

    _model_name = Unicode("IpylabModel", help="Name of the model.", read_only=True).tag(sync=True)
    _basename = Unicode(allow_none=True).tag(sync=True)
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
        await self.wait_ready()
        self._check_closed()

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def close(self):
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

    # TODO: Add better type hints (pass the result of the coro)
    def to_task(self, coro: Coroutine):
        """Run the coro in a task."""

        self._check_closed()
        task = asyncio.create_task(self._wrap_coro(coro))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    # TODO: Add better type hints (pass the result of the coro)
    async def _wrap_coro(self, coro: Coroutine):
        try:
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
                    msg += "\nNote: Additional information may be available in the browser console (press `F12`)"
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
        if content["transform"] is TransformMode.connection:
            from ipylab.disposable_connection import DisposableConnection

            return DisposableConnection(**payload)
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
                self.to_task(self._handle_frontend_operation(content["ipylab_FE"], operation, payload, buffers))
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

    def schedule_operation(
        self,
        operation: str,
        *,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
        **kwgs,
    ):
        """Create a new task requesting an operation to be performed in the frontend.

        operation: str
            Name corresponding to operation in JS frontend.

        transform : TransformMode | dict
            see ipylab.TransformMode

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
            kwgs are also available to the transform.
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
        return self.to_task(self._send_receive(content))

    def execute_method(
        self,
        path: str,
        *args,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
        **kwgs,
    ):
        """Call a method on the corresponding frontend object.

        path: 'dotted.access.to.the.method' relative to obj.

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
            **kwgs,
        )

    def get_attribute(self, path: str, *, transform: TransformType = TransformMode.raw, nullIfMissing=False):
        """Obtain a serialized version of the attribute relative to this object.

        Tip: This method will await the attribute in the Frontend prior to returning the result
        where the attribute is an awaitable.
        """
        return self.schedule_operation("getAttribute", path=path, nullIfMissing=nullIfMissing, transform=transform)

    def set_attribute(
        self,
        path: str,
        value,
        *,
        value_transform: TransformType | dict = TransformMode.raw,
        value_transform_kwgs: None | dict = None,
        value_toLuminoWidget=False,
        transform=TransformMode.done,
    ):
        """Set the attribute at the path in the frontend.
        path: str
            "the.path.to.the.attribute" to be set.
        value: jsonable
            The value to set, or instructions for the transform to do in the frontend.
        valueTransform: TransformType
            valueTransform is applied to the value prior to setting the attribute.
            It may be specified as a dict with the mapping: transform:TransformType.<value>
        value_toLuminoWidget: bool
            Whether the value should be converted to a Lumino widget. The value transform
            can be left as raw unless further adanced transformation is required.
        """
        vt = dict(value_transform_kwgs) if value_transform_kwgs else {}
        vt["transform"] = TransformMode(value_transform)
        return self.schedule_operation(
            "setAttribute",
            path=path,
            value=pack(value),
            valueTransform=vt,
            toLuminoWidget=["value"] if value_toLuminoWidget else None,
            transform=transform,
        )

    def update_values(self, path: str, values: dict, *, toLuminoWidget: Iterable[str] | None = None):
        """Update the values of the object at the path in the frontend.
        path: str
            "the.path.to.the.attribute" to be set.
        toLuminoWidget:
            Dotted attribute names to convert to LuminoWidgets in the frontend.
            eg. ["values.value_toLuminoWidget"]
        """
        return self.schedule_operation(
            "updateValues", path=path, values=values, transform=TransformMode.raw, toLuminoWidget=toLuminoWidget
        )

    def list_attributes(
        self,
        path: str = "",
        type: JavascriptType = JavascriptType.function,  # noqa: A002
        depth=2,
        *,
        how: Literal["names", "group", "raw"] = "group",
        transform: TransformType = TransformMode.raw,
        skip_hidden=True,
    ) -> Task[dict | list]:
        """Get a mapping of attributes of the object at 'path' of the Frontend instance.

        depth: The depth in the object inheritance to search for attributes.
        how: ['names', 'group', 'raw']
        """
        task = self.schedule_operation("listAttributes", path=path, type=type, depth=depth, transform=transform)

        async def list_attributes_():
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

        return self.to_task(list_attributes_())  # type: ignore

    def list_methods(self, path: str = "", *, depth=2, skip_hidden=True):
        """Get a list of methods belonging to the object 'path' of the Frontend instance.
        depth: The depth in the object inheritance to search for methods.
        """
        task = self.list_attributes(path, JavascriptType.function, depth, how="names")

        async def _list_methods():
            payload = (await task) or []
            if skip_hidden:
                return [n for n in payload if not n.startswith("_")]
            return payload

        return self.to_task(_list_methods())
