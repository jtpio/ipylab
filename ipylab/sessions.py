# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.


import asyncio

from traitlets import Dict, Tuple, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, register


@register
class SessionManager(AsyncWidgetBase):
    """Expose JupyterFrontEnd.serviceManager.sessions"""

    _model_name = Unicode("SessionManagerModel").tag(sync=True)
    SINGLETON = True
    # information of the session in which the application is started
    app_session = Dict(read_only=True).tag(sync=True)
    # information of the current session
    current_session = Dict(read_only=True).tag(sync=True)
    # keeps track of the list of sessions
    sessions = Tuple(read_only=True).tag(sync=True)

    def refresh_running(self) -> asyncio.Task:
        """Force a call to refresh running sessions."""
        return self.schedule_operation("refreshRunning")


# Start session to get app session
# Is there a better way to get the session where this code is running?
SessionManager()
