# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from ipylab._version import __version__

__all__ = [
    "__version__",
    "HasApp",
    "JupyterFrontEnd",
    "Connection",
    "MainAreaConnection",
    "Panel",
    "SplitPanel",
    "Icon",
    "Area",
    "InsertMode",
    "hookimpl",
    "Transform",
    "pack",
    "pack_code",
    "commands",
    "menu",
]

from ipylab import commands, menu
from ipylab.asyncwidget import pack, pack_code
from ipylab.common import Area, InsertMode, Transform
from ipylab.connection import Connection, MainAreaConnection
from ipylab.hasapp import HasApp
from ipylab.hookspecs import hookimpl
from ipylab.jupyterfrontend import JupyterFrontEnd
from ipylab.widgets import Icon, Panel, SplitPanel


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
