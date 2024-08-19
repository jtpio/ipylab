# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio

from ipylab.jupyterfrontend_subsection import FrontEndSubsection


class SessionManager(FrontEndSubsection):
    """
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html
    """

    SUB_PATH_BASE = "app.sessionManager"

    def refreshRunning(self) -> asyncio.Task:
        """Force a call to refresh running sessions."""
        return self.execute_method("refreshRunning")

    def stopIfNeeded(self, path) -> asyncio.Task:
        """
        https://jupyterlab.readthedocs.io/en/latest/api/interfaces/services.Session.IManager.html#stopIfNeeded
        """
        return self.execute_method("stopIfNeeded", path)
