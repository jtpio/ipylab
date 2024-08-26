# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from asyncio import Task
from types import ModuleType

from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, Unicode, pack_code
from ipylab.disposable_connection import DisposableConnection


class SessionManager(AsyncWidgetBase):
    """
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html
    """

    SINGLETON = True
    _basename = Unicode("app.sessionManager").tag(sync=True)

    def refreshRunning(self):
        """Force a call to refresh running sessions."""
        return self.execute_method("refreshRunning")

    def stopIfNeeded(self, path):
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
        kernelName="python3",
        code: str | ModuleType = "",
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
        return self.app.schedule_operation(
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
        self, path: str = "", *, name: str = "", kernelId="", kernelName="python3", code: str | ModuleType = ""
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
