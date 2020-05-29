"""Expose current and all sessions to python kernel
"""

from ipywidgets import Widget, register
from traitlets import List, Unicode, Dict

from ._frontend import module_name, module_version


def _noop():
    pass

@register
class SessionManager(Widget):
    """Expose JupyterFrontEnd.serviceManager.sessions"""

    _model_name = Unicode("SessionManagerModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    # keeps track of alist of sessions
    current_session = Dict(read_only=True).tag(sync=True)
    sessions = List([], read_only=True).tag(sync=True)

    def get_current_session(self):
        """Force a call to update current session"""
        self.send({"func": "get_current"})

    def list_sessions(self):
        """List all running sessions managed in the manager"""
        return self.sessions
