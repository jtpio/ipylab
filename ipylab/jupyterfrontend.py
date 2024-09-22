# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from traitlets import Container, Dict, Instance, Tuple, Unicode, observe

from ipylab import ShellConnection
from ipylab.asyncwidget import AsyncWidgetBase, Transform, pack, pack_code, register, widget_serialization
from ipylab.commands import CommandRegistry
from ipylab.dialog import Dialog, FileDialog
from ipylab.menu import MainMenu
from ipylab.notification import NotificationManager
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    from ipylab.asyncwidget import TransformType


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

    @observe("all_shell_connections_info")
    def _observe_all_shell_connections_info(self, _):
        connections = []
        for info in self.all_shell_connections_info:
            if info["kernelId"] == self.kernelId:
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
            case "execEval":
                return await self._exec_eval(payload, buffers)
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def shutdown_kernel(self, kernelId: str | None = None):
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    def exec_eval(
        self,
        execute: str | inspect._SourceObjectType,
        evaluate: dict[str, str],
        kernelId="",
        frontend_transform: TransformType = Transform.done,
        **kwgs,
    ):
        """Execute and evaluate code in the Python kernel with the id `kernelId`.

        If `kernelId` isn't provided a new kernel will be created. kwgs are provided to the new session.

        execute:
            The code as text or function to executed.
            ref: https://docs.python.org/3/library/functions.html#exec
        eval:
            A dictionary of `symbol name` to `expression` mappings to be evaluated in the kernel.
            Each expression is evaluated in turn adding the symbol to the namespace. The evaluation
            of the expression will also be called and or awaited until the returned symbol is no
            longer callable or awaitable.

            ref: https://docs.python.org/3/library/functions.html#eval

            Once evaluation is complete, the symbols named `payload` and `buffers` will be sent
            back (if they were defined).
        kernelId:
            The Id allocated to the kernel in the frontend.
        frontend_transform: TransformType
            The transform to use in the frontend on the payload returned from evaluation.
        """

        code = "import ipylab; ipylab.JupyterFrontEnd()"
        task = None if kernelId else self.session_manager.new_sessioncontext(code=code, **kwgs)
        frontend_transform = Transform.validate(frontend_transform)

        async def exec_eval_():
            k_id = kernelId
            if task:
                connection = await task
                k_id = await connection.get_attribute("session.kernel.id")
            return await self.app.schedule_operation(
                "execEval",
                code=pack_code(execute),
                evaluate=dict(evaluate),
                kernelId=k_id,
                frontendTransform=frontend_transform,
            )

        return self.to_task(exec_eval_())

    async def _exec_eval(self, payload: dict, buffers: list) -> Any:
        """exec/eval code corresponding to a call from execEval, likely from
        another kernel."""
        # TODO: consider if globals / locals / async scope should be supported.
        code = payload.get("code")
        glbls = payload | {"buffers": buffers}
        if code:
            exec(code, glbls)  # noqa: S102
        for name, expression in payload.get("evaluate", {}).items():
            result = eval(expression, glbls)  # noqa: S307
            while callable(result) or inspect.isawaitable(result):
                if callable(result):
                    result = result()
                if inspect.isawaitable(result):
                    result = await result
            glbls[name] = result
        return {"payload": pack(glbls.get("payload")), "buffers": glbls.get("buffers", [])}

    def checkstart_iyplab_python_backend(self, *, restart=False):
        """Checks backend is running and starts it if it isn't, returning the session model."""
        return self.schedule_operation("startIyplabPythonBackend", restart=restart, transform=Transform.done)
