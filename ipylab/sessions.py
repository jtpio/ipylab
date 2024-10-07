# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from asyncio import Task
from types import ModuleType
from typing import Literal

from ipylab.connection import Connection
from ipylab.ipylab import Ipylab, Transform, Unicode


class SessionManager(Ipylab):
    """
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html
    """

    SINGLETON = True
    _basename = Unicode("app.serviceManager.sessions").tag(sync=True)

    def refresh_running(self):
        """Force a call to refresh running sessions."""
        return self.execute_method("refreshRunning")

    def stop_if_needed(self, path):
        """
        https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html#stopIfNeeded
        """
        return self.execute_method("stopIfNeeded", path)

    def new_sessioncontext(
        self,
        path: str = "",
        *,
        name: str = "",
        kernelId="",
        language="python",
        code: str | ModuleType = "",
        type: Literal["console", "notebook"] = "console",  # noqa: A002
        ensureFrontend=True,
    ) -> Task[Connection]:
        """
        Create a new sessionContext.


        path: The session path.
        name: The name of the session.
        language: language for kernel prefrences.
        code: A string, module or function to be called in the kernel.
        type: The type of session.
        ensureFrontend: Ensures a frontend has been started.
        """
        return self.app.schedule_operation(
            "newSessionContext",
            path=path,
            name=name or path,
            kernelId=kernelId,
            language=language,
            type=type,
            code=code,
            ensureFrontend=ensureFrontend,
            transform=Transform.connection,
        )
