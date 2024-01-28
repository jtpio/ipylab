# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio
import inspect
from typing import Callable

from ipylab.asyncwidget import TransformMode
from ipylab.jupyterfrontend_subsection import JupyterFrontEndSubsection


class SessionManager(JupyterFrontEndSubsection):
    """
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html
    """

    JFE_JS_SUB_PATH = "app.sessionManager"

    def refreshRunning(self) -> asyncio.Task:
        """Force a call to refresh running sessions."""
        return self.execute_method("refreshRunning")

    def stopIfNeeded(self, path) -> asyncio.Task:
        """
        https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html#stopIfNeeded
        """
        return self.execute_method("stopIfNeeded", path=path)

    def startNew(
        self,
        path: str,
        type: str,
        name: str,
        *,
        kernel: dict | None = None,
        createOptions={},
        connectOptions={},
        code: str | Callable | None = None,
        transform=TransformMode.raw,
    ) -> asyncio.Task:
        """
        Create a new kernel and execute code in it.

        https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html#startNew

        If specifying kernel. Use kernel = {'id':kernel_id}
        """
        createOptions = dict(path=path, type=type, name=name) | createOptions
        connectOptions = dict(kernel=kernel) | connectOptions

        if callable(code):
            code = inspect.getsource(code)

        return self.app.schedule_operation(
            "startNewSessionExecuteCode",
            createOptions=createOptions,
            connectOptions=createOptions,
            transform=transform,
            code=code,
        )
