# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from ipylab._version import __version__

__all__ = [
    "__version__",
    "Connection",
    "ShellConnection",
    "Panel",
    "SplitPanel",
    "Icon",
    "Area",
    "NotificationType",
    "InsertMode",
    "hookimpl",
    "Transform",
    "pack",
    "_jupyter_labextension_paths",
]
import ipylab.commands as _commands  # noqa: F401
from ipylab.common import Area, InsertMode, NotificationType, Transform, pack
from ipylab.connection import Connection, ShellConnection
from ipylab.hookspecs import hookimpl
from ipylab.widgets import Icon, Panel, SplitPanel


def _jupyter_labextension_paths():
    "Called by Jupyterlab see: jupyterlab.federated_labextensions._get_labextension_metadata."
    return [{"src": "labextension", "dest": "ipylab"}]


def _get_app():
    "Get the frontend"
    from ipylab.jupyterfrontend import JupyterFrontEnd

    return JupyterFrontEnd()


# The Frontend should always be created and can not be subclassed.
app = _get_app()
del _get_app
