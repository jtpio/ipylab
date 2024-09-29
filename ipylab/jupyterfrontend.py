# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any

import ipywidgets as ipw
from traitlets import Container, Dict, Instance, Tuple, Unicode, observe

import ipylab
from ipylab import ShellConnection, Transform
from ipylab.asyncwidget import AsyncWidgetBase, register, widget_serialization
from ipylab.commands import CommandRegistry
from ipylab.dialog import Dialog, FileDialog
from ipylab.menu import MainMenu
from ipylab.notification import NotificationManager
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    from collections.abc import Iterable


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
    menu = Instance(MainMenu, ())
    notification = Instance(NotificationManager, ())

    def __init_subclass__(cls, **kwargs) -> None:
        msg = "Subclassing the `JupyterFrontEnd` class is not allowed!"
        raise RuntimeError(msg)

    def close(self):
        "Cannot close"

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
    def current_widget(self):
        """A connection to the current widget in the shell."""
        id_ = self.current_widget_id
        return ShellConnection(cid=ShellConnection.to_cid(id_), id=id_)

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "evaluate":
                return await self._evaluate(payload, buffers)
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def shutdown_kernel(self, kernelId: str | None = None):
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    # TODO: move to AsyncWidgetBase maybe. Maybe use a path instead of a kernel or find the kernel by the path
    def evaluate(
        self, evaluate: dict[str, str | inspect._SourceObjectType] | str, *, kernelId="", path="", name="", **kwgs
    ):
        """Evaluate code in a Python kernel.

        If `kernelId` isn't provided a session matching the path will be used, possibly prompting for a kernel.
            **kwgs are used when creating a new session context.
                name: name of the new session.
                path: path of the session context.

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

    async def _evaluate(self, options: dict, buffers: list) -> Any:
        """Evaluate code corresponding to a call from 'evaluate'.

        A call to this method should originate from either:
         1. An `evaluate` method call from a subclass of `AsyncWidgetBase`.
         2. A direct call in the frontend at jfem.evaluate.

        """
        glbls = {"ipylab": ipylab, "ipywidgets": ipw, "ipw": ipw} | options | {"buffers": buffers}
        evaluate = options.get("evaluate", {})
        if isinstance(evaluate, str):
            evaluate = {"payload": evaluate}
        for name, expression in evaluate.items():
            try:
                result = eval(expression, glbls)  # noqa: S307
            except SyntaxError:
                exec(expression, glbls)  # noqa: S102
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
        return {"payload": glbls.get("payload"), "buffers": glbls.get("buffers", [])}

    def checkstart_iyplab_python_backend(self, *, restart=False):
        """Checks backend is running and starts it if it isn't, returning the session model."""
        return self.schedule_operation("startIyplabPythonBackend", restart=restart, transform=Transform.raw)
