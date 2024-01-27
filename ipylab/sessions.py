# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio

from ipylab.asyncwidget import TransformMode
from ipylab.sub import SubApp


class SessionManager(SubApp):
    """
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html
    """

    SUBPATH = "sessionManager"

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
        transform={"mode": TransformMode.attribute, "parts": ["model"]},
    ) -> asyncio.Task:
        """
        https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html#startNew

        If specifying kernel. Use kernel = {'id':kernel_id}
        """
        createOptions = dict(path=path, type=type, name=name) | createOptions
        connectOptions = dict(kernel=kernel) | connectOptions
        return self.execute_method("startNew", createOptions, connectOptions, transform=transform)
