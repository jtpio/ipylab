# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from traitlets import Dict, Instance, Tuple, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack, pack_code, register, widget_serialization
from ipylab.commands import CommandPalette, CommandRegistry, Launcher
from ipylab.dialog import Dialog, FileDialog
from ipylab.hookspecs import pm
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    import types
    from asyncio import Task

    from ipylab.disposable_connection import DisposableConnection


@register
class JupyterFrontEnd(AsyncWidgetBase):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    SINGLETON = True

    version = Unicode(read_only=True).tag(sync=True)
    commands = Instance(CommandRegistry, (), read_only=True).tag(sync=True, **widget_serialization)
    command_pallet = Instance(CommandPalette, (), read_only=True).tag(sync=True, **widget_serialization)
    launcher = Instance(Launcher, (), read_only=True).tag(sync=True, **widget_serialization)

    current_widget_id = Unicode(read_only=True).tag(sync=True)
    current_session = Dict(read_only=True).tag(sync=True)
    all_sessions = Tuple(read_only=True).tag(sync=True)

    @property
    def dialog(self) -> Dialog:
        if not hasattr(self, "_dialog"):
            self._dialog = Dialog()
        return self._dialog

    @property
    def file_dialog(self) -> FileDialog:
        if not hasattr(self, "_fileDialog"):
            self._fileDialog = FileDialog()
        return self._fileDialog

    @property
    def shell(self) -> Shell:
        if not hasattr(self, "_shell"):
            self._shell = Shell()
        return self._shell

    @property
    def sessionManager(self) -> SessionManager:
        if not hasattr(self, "_sessionManger"):
            self._sessionManger = SessionManager()
        return self._sessionManger

    async def wait_ready(self, timeout=5):  # noqa: ASYNC109
        """Wait until connected to app indicates it is ready."""
        if not self._ready_response.is_set():
            future = asyncio.gather(
                super().wait_ready(),
                self.commands.wait_ready(),
                self.command_pallet.wait_ready(),
                self.launcher.wait_ready(),
            )
            await asyncio.wait_for(future, timeout)
        return self

    def _init_python_backend(self):
        "Run by the Ipylab python backend."
        # This is called in a separate kernel started by the JavaScript frontend
        # the first time the ipylab plugin is activated.
        from ipylab.hookspecs import pm

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
            case _:
                pm.hook.unhandled_frontend_operation_message(obj=self, operation=operation)
        raise NotImplementedError

    def shutdown_kernel(self, kernelId: str | None = None):
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    def new_sessioncontext(
        self,
        path: str = "",
        *,
        name: str = "",
        kernelId="",
        kernelName="python3",
        code: str | types.ModuleType = "",
        type="console",  # noqa: A002
    ) -> Task[DisposableConnection]:
        """
        Create a new sessionContext, potentiall with a new session and kernel.

        path: The session path.
        name: The name of the session.
        kernelName: The name of the kernel (only Python kernel implemented).
        code: A string, module or function.
        type: The type of session.

        If passing a function, the function will be executed. It is important
        that objects that must stay alive outside the function must be kept alive.
        So it is advised to use a code.

        """
        return self.schedule_operation(
            "newSessionContext",
            path=path,
            name=name or path,
            kernelId=kernelId,
            kernelName=kernelName,
            type=type,
            code=pack_code(code),
            transform=TransformMode.connection,
        )

    def new_notebook(
        self, path: str = "", *, name: str = "", kernelId="", kernelName="python3", code: str | types.ModuleType = ""
    ) -> Task[DisposableConnection]:
        """Create a new notebook."""
        return self.schedule_operation(
            "newNotebook",
            path=path,
            name=name or path,
            kernelId=kernelId,
            kernelName=kernelName,
            code=pack_code(code),
            transform=TransformMode.connection,
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
        task = None if kernelId else self.new_sessioncontext(code="import ipylab; ipylab.JupyterFrontEnd()", **kwgs)

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
