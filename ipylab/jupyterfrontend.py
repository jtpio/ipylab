# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import functools
import inspect
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

import ipywidgets
from IPython.core.getipython import get_ipython
from ipywidgets import widget_serialization
from traitlets import Container, Dict, Instance, Tuple, Unicode, observe

import ipylab
from ipylab import ShellConnection, Transform
from ipylab.asyncwidget import AsyncWidgetBase, register
from ipylab.commands import CommandRegistry
from ipylab.common import InsertMode
from ipylab.dialog import Dialog, FileDialog
from ipylab.hookspecs import pm
from ipylab.menu import ContextMenu, MainMenu
from ipylab.notification import NotificationManager
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Iterable
    from typing import ClassVar


class LastUpdatedOrderedDict(OrderedDict):
    "Store items in the order the keys were last added"

    # ref: https://docs.python.org/3/library/collections.html#ordereddict-examples-and-recipes

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)


@register
class JupyterFrontEnd(AsyncWidgetBase):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    _basename = Unicode("app", read_only=True).tag(sync=True)
    SINGLETON = True
    version = Unicode(read_only=True).tag(sync=True)
    commands = Instance(CommandRegistry, (), read_only=True).tag(sync=True, **widget_serialization)
    current_widget_id = Unicode(read_only=True).tag(sync=True)
    current_session = Dict(read_only=True).tag(sync=True)
    all_sessions = Tuple(read_only=True).tag(sync=True)
    all_shell_connections_info: Container[tuple[dict, ...]] = Tuple(read_only=True).tag(sync=True)
    shell_connections: Container[tuple[ShellConnection, ...]] = Tuple(read_only=True)
    dialog = Instance(Dialog, (), read_only=True)
    file_dialog = Instance(FileDialog, (), read_only=True)
    shell = Instance(Shell, (), read_only=True)
    session_manager = Instance(SessionManager, (), read_only=True)
    main_menu = Instance(MainMenu, ())
    context_menu = Instance(ContextMenu, ())
    notification = Instance(NotificationManager, ())
    active_namespace = Unicode("", read_only=True, help="name of the current namespace")
    namespace_defaults = Dict({"ipylab": ipylab, "ipywidgets": ipywidgets, "ipw": ipywidgets})
    _namespaces: Container[dict[str, LastUpdatedOrderedDict]] = Dict(read_only=True)  # type: ignore
    namespaces: Container[tuple[str, ...]] = Tuple(read_only=True).tag(sync=True)
    _ipy_shell = get_ipython()
    _ipy_default_namespace: ClassVar = getattr(_ipy_shell, "user_ns", {})

    def __init_subclass__(cls, **kwargs) -> None:
        msg = "Subclassing the `JupyterFrontEnd` class is not allowed!"
        raise RuntimeError(msg)

    def close(self):
        "Cannot close"

    def on_frontend_init(self, content: dict):
        super().on_frontend_init(content)
        pm.hook.on_app_ready()

    def _gen_repr_from_keys(self, keys: Iterable):  # noqa: ARG002
        return super()._gen_repr_from_keys(("kernelId",))

    @observe("all_shell_connections_info")
    def _observe_all_shell_connections_info(self, _):
        connections = []
        for info in self.all_shell_connections_info:
            if info.get("kernelId") == self.kernelId:
                conn = ShellConnection(cid=info["cid"], id=info["id"], info=info)
                connections.append(conn)
        self.set_trait("shell_connections", connections)

    @property
    def current_widget(self) -> ShellConnection:
        """A connection to the current widget in the shell."""
        id_ = self.current_widget_id
        return ShellConnection(cid=ShellConnection.to_cid(id_), id=id_)

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "evaluate":
                return await self._evaluate(payload, buffers)
            case "open console":
                return await self.open_console(**payload)
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def shutdown_kernel(self, kernelId: str | None = None):
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    def checkstart_iyplab_python_backend(self, *, restart=False):
        """Checks backend is running and starts it if it isn't, returning the session model."""
        return self.schedule_operation("startIyplabPythonBackend", restart=restart, transform=Transform.raw)

    # TODO: move to AsyncWidgetBase maybe. Maybe use a path instead of a kernel or find the kernel by the path
    def evaluate(
        self, evaluate: dict[str, str | inspect._SourceObjectType] | str, *, kernelId="", path="", name="", **kwgs
    ):
        """Evaluate code in a Python kernel.

        If `kernelId` isn't provided a session matching the path will be used, possibly prompting for a kernel.
            **kwgs are used when creating a new session namespace.
                name: name of the new session.
                path: path of the session namespace.

        evaluate:
            An expression to evaluate or execute.

            The evaluation expression will also be called and or awaited until the returned symbol is no
            longer callable or awaitable.
            String:
                If it is string it will be evaluated and returned.
            Dict: Advanced usage:
            A dictionary of `symbol name` to `expression` mappings to be evaluated in the kernel.
            Each expression is evaluated in turn adding the symbol to the namespace.

            Expression can be a the name of a function or class. In which case it will be evaluated
            using parameter names matching the signature of the function or class.

            ref: https://docs.python.org/3/library/functions.html#eval

            Once evaluation is complete, the symbols named `payload` and `buffers` will be returned.
        kernelId:
            The Id allocated to the kernel in the frontend.
        globals:
            The globals namespace includes the follow symbols:
            * ipylab
            * ipywidgets
            * ipw (ipywidgets)
        """
        return self.app.schedule_operation(
            "evaluate", evaluate=evaluate, kernelId=kernelId, path=path, name=name, **kwgs
        )

    def _get_namespace(self, path=""):
        "Get the 'globals' namespace stored for path."
        if path not in self._namespaces:
            self._namespaces[path] = LastUpdatedOrderedDict(self._ipy_default_namespace | self.namespace_defaults)
            self.set_trait("namespaces", tuple(self.namespaces))
        self._namespaces[path]["app"] = self
        return self._namespaces[path]

    def update_namespace(self, path: str, glbls: dict, *, activate=False):
        "Update the namespace for the path"
        self._get_namespace(path).update(glbls)
        if activate:
            self.activate_namespace(path)

    def activate_namespace(self, path: str):
        "Sets the ipython/console namespace to the one corresponding to path."
        if not self._ipy_shell:
            msg = "Ipython shell is not loaded!"
            raise RuntimeError(msg)
        self._ipy_shell.user_ns = self._get_namespace(path)
        self.set_trait("active_namespace", path)
        self._ipy_shell.push({})

    def reset_namespace(self, path: str, *, activate=True):
        "Reset the namespace to default. If activate is False it won't be created."
        self._namespaces.pop(path, None)
        if activate:
            self.activate_namespace(path)
        else:
            self.set_trait("namespaces", tuple(self.namespaces))

    def open_console(
        self,
        path="",
        *,
        insertMode=InsertMode.split_bottom,
        namespace_name="",
        activate=True,
        **args,
    ) -> Task[ShellConnection]:
        """Open a console and activate the namespace.

        path: str
            The path of the session context and default namespace_name.

        namespace_name: str
            An alternate namespace to activate.
        """
        args["path"] = path
        args["insertMode"] = insertMode

        async def open_console():
            self.activate_namespace(namespace_name or path)
            return await self.execute_command(
                "console:open",
                activate=activate,
                **args,
                transform={"transform": Transform.connection, "cid": ShellConnection.to_cid("console", "path")},
            )

        return self.to_task(open_console())

    async def _evaluate(self, options: dict, buffers: list) -> Any:
        """Evaluate code corresponding to a call from 'evaluate'.

        A call to this method should originate from either:
         1. An `evaluate` method call from a subclass of `AsyncWidgetBase`.
         2. A direct call in the frontend at jfem.evaluate.

        """
        path = options.get("path", "")
        glbls = self._get_namespace(path) | options | {"buffers": buffers}
        evaluate = options.get("evaluate", {})
        if isinstance(evaluate, str):
            evaluate = {"payload": evaluate}
        for name, expression in evaluate.items():
            try:
                result = eval(expression, glbls, glbls)  # noqa: S307
            except SyntaxError:
                exec(expression, glbls, glbls)  # noqa: S102
                result = next(reversed(glbls.values()))
            while callable(result) or inspect.isawaitable(result):
                if callable(result):
                    pnames = set(glbls).intersection(inspect.signature(result).parameters)
                    kwgs = {name: glbls[name] for name in pnames}
                    glbls[name] = functools.partial(result, **kwgs)
                    result = eval(f"{name}()", glbls)  # type: ignore # noqa: S307
                if inspect.isawaitable(result):
                    result = await result
            glbls[name] = result
        buffers = glbls.pop("buffers", [])
        self.update_namespace(path, glbls)
        return {"payload": glbls.get("payload"), "buffers": buffers}
