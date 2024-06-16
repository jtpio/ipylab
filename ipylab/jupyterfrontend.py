# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from traitlets import Dict, Instance, Tuple, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack_code, register, widget_serialization
from ipylab.commands import CommandPalette, CommandRegistry, Launcher
from ipylab.dialog import Dialog, FileDialog
from ipylab.hookspecs import pm
from ipylab.sessions import SessionManager
from ipylab.shell import Shell

if TYPE_CHECKING:
    import types
    from collections.abc import Callable


@register
class JupyterFrontEnd(AsyncWidgetBase):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    SINGLETON = True

    version = Unicode(read_only=True).tag(sync=True)
    command = Instance(CommandRegistry, (), read_only=True).tag(sync=True, **widget_serialization)
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

    async def wait_ready(self, timeout=5):
        """Wait until connected to app indicates it is ready."""
        if not self._ready_response.is_set():
            future = asyncio.gather(
                super().wait_ready(),
                self.command.wait_ready(),
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
                return await self._execEval(payload, buffers)
            case _:
                pm.hook.unhandled_frontend_operation_message(obj=self, operation=operation)
        raise NotImplementedError

    def shutdownKernel(self, kernelId: str | None = None) -> asyncio.Task:
        """Shutdown the kernel"""
        return self.schedule_operation("shutdownKernel", kernelId=kernelId)

    def newSession(
        self,
        path: str = "",
        *,
        name: str = "",
        kernelId="",
        kernelName="python3",
        code: str | types.ModuleType = "",
        type="ipylab",  # noqa: A002
    ) -> asyncio.Task:
        """
        Create a new kernel and execute code in it or execute code in an existing kernel.

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
            "newSession",
            path=path,
            name=name or path,
            kernelId=kernelId,
            kernelName=kernelName,
            type=type,
            code=pack_code(code),
            transform=TransformMode.raw,
        )

    def newNotebook(
        self, path: str = "", *, name: str = "", kernelId="", kernelName="python3", code: str | types.ModuleType = ""
    ) -> asyncio.Task:
        """Create a new notebook."""
        return self.schedule_operation(
            "newNotebook",
            path=path,
            name=name or path,
            kernelId=kernelId,
            kernelName=kernelName,
            code=pack_code(code),
            transform=TransformMode.raw,
        )

    def injectCode(
        self, kernelId: str, code: str | types.ModuleType, user_expressions: dict[str, str | types.ModuleType] | None
    ) -> asyncio.Task:
        """
        Inject code into a running kernel using the Jupyter builtin `requestExecute`.

        This is equivalent to running code in a notebook cell and the same rules apply.
        Use `execEval` instead to wait for the result of asynchronous code.

        kernelId: Jupyterlab assigned ID of running kernel to inject the code into.

        code: str | code
            If passing a function, the function will be executed when its injected.

        user_expressions: dict
            mapping of key to an eval expression (awaitiable objects are awaited.)
            The result of the user expression is returned in the payload. It must be
            jsonizable.
        """

        return self.schedule_operation(
            "injectCode",
            kernelId=kernelId,
            code=pack_code(code),
            user_expressions=user_expressions,
            transform=TransformMode.raw,
        )

    def execEval(
        self,
        code: str | types.ModuleType | Callable,
        user_expressions: dict[str, str | types.ModuleType] | None,
        kernelId="",
        **kwgs,
    ) -> asyncio.Task:
        """Execute and evaluate code in the Python kernel corresponding to kerenelId, or create a new kernel
        if `kernelId` isn't provided.

        When kernelId is not passed (default) a new session is created the same way a new session is
        created (Addnl kwgs).

        This function is similar to `injectCode` in functionality but avoids blocking kernel comms. It
        will only work in a python kernel where the widgets have been enabled.

        Handling of execution is performed by `_execEval` of the `JupyterFrontEnd` instance running in
        the kernel with kernelId.

        exec:
            The code as a script or function to pass to the builtin `exec`, returns `None`.
            ref: https://docs.python.org/3/library/functions.html#exec
        eval:
            An expression to evalate using the builtin `eval`.
            If the evaluation returns an executable, it will be executed. I the
            result is awaitable, the result will be awaited.
            The serialized result or result of the awaitable will be returned via the frontend.
            ref: https://docs.python.org/3/library/functions.html#eval
        kernelId:
            The Id allocated to the kernel in the frontend.
        Addnl kwgs:
            path, name, type='ipylab' | 'notebook' | 'console' for a new session.
        """
        return self.app.schedule_operation(
            "execEval",
            code=pack_code(code),
            user_expressions=user_expressions,
            kernelId=kernelId,
            **kwgs,
        )

    async def _execEval(self, payload: dict, buffers: list) -> Any:
        """exec/eval code corresponding to a call from execEval, likely from
        another kernel."""
        # TODO: consider if globals / locals / async scope should be supported.
        code = payload.get("code")
        user_expressions = payload.get("user_expressions") or {}
        locals_ = payload | {"buffers": buffers}
        if code:
            exec(code, None, locals_)  # noqa: S102
        if user_expressions:
            results = {}
            for name, expression in user_expressions.items():
                result = eval(expression, None, locals_)  # noqa: S307
                if callable(result):
                    result = result()
                if inspect.isawaitable(result):
                    result = await result
                results[name] = result
            return results
        return None

    def startIyplabPythonBackend(self) -> asyncio.Task:
        """Checks backend is running and starts it if it isn't, returning the session model."""
        return self.schedule_operation("startIyplabPythonBackend")
