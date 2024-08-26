# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from traitlets import Dict, Instance, Tuple, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack, pack_code, register, widget_serialization
from ipylab.commands import CommandRegistry
from ipylab.dialog import Dialog, FileDialog
from ipylab.hookspecs import pm
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    from collections.abc import Iterable

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
    dialog = Instance(Dialog, (), read_only=True)
    file_dialog = Instance(FileDialog, (), read_only=True)
    shell = Instance(Shell, (), read_only=True)
    session_manager = Instance(SessionManager, (), read_only=True)

    def _init_python_backend(self):
        "Run by the Ipylab python backend."
        # This is called in a separate kernel started by the JavaScript frontend
        # the first time the ipylab plugin is activated.

        try:
            count = pm.load_setuptools_entrypoints("ipylab_backend")
            self.log.info("Ipylab python backend found {%} plugin entry points.", count)
        except Exception as e:
            self.log.exception("An exception occurred when loading plugins")
            self.dialog.show_error_message("Plugin failure", str(e))

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "execEval":
                return await self._exec_eval(payload, buffers)
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def shutdown_kernel(self, kernelId: str | None = None):
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    def execute_command(
        self,
        command_id: str,
        *,
        transform: TransformType = TransformMode.done,
        toLuminoWidget: Iterable[str] | None = None,
        **kwgs,
    ):
        """Execute the command_id registered with Jupyterlab.

        `kwgs` correspond to `args` in JupyterLab.

        execute_kwgs: dict | None
            Passed to execute_method (we use a dict to avoid any potential of argument clash).

        Finding what `args` can be used remains an outstanding issue in JupyterLab.

        see: https://github.com/jtpio/ipylab/issues/128#issuecomment-1683097383 for hints
        about how args can be found.
        """
        return self.execute_method(
            "commands.execute",
            command_id,
            kwgs,  # -> used as 'args' in Jupyter
            transform=transform,
            toLuminoWidget=toLuminoWidget,
        )

    def exec_eval(self, execute: str | inspect._SourceObjectType, evaluate: dict[str, str], kernelId="", **kwgs):
        """Execute and evaluate code in the Python kernel corresponding to kerenelId.

        If `kernelId` isn't provided a new session will be launched. kwgs are used for the new session.

        execute:
            The code as a script or function to pass to the builtin `exec`, returns `None`.
            ref: https://docs.python.org/3/library/functions.html#exec
        eval:
            An expression to evaluate using the builtin `eval`.
            If the evaluation returns an executable, it will be executed. I the
            result is awaitable, the result will be awaited.
            The serialized result or result of the awaitable will be returned via the frontend.
            ref: https://docs.python.org/3/library/functions.html#eval
        kernelId:
            The Id allocated to the kernel in the frontend.
        Addnl kwgs:
            path, name, type='notebook' | 'console' for a new session.
        """

        code = "import ipylab; ipylab.JupyterFrontEnd()"
        task = None if kernelId else self.session_manager.new_sessioncontext(code=code, **kwgs)

        async def execEval_():
            k_id = kernelId
            if task:
                connection = await task
                k_id = await connection.get_attribute("session.kernel.id")
            return await self.app.schedule_operation(
                "execEval", code=pack_code(execute), evaluate=evaluate, kernelId=k_id
            )

        return self.to_task(execEval_())

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
        return self.schedule_operation("startIyplabPythonBackend", restart=restart, transform=TransformMode.connection)
