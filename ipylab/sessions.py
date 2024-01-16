# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.


from traitlets import Dict, Tuple, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, register


@register
class SessionManager(AsyncWidgetBase):
    """Expose JupyterFrontEnd.serviceManager.sessions"""

    _model_name = Unicode("SessionManagerModel").tag(sync=True)
    SINGLETON = True

    # information of the current session
    current_session = Dict(read_only=True).tag(sync=True)
    # keeps track of the list of sessions
    sessions = Tuple(read_only=True).tag(sync=True)
