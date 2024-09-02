# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from ipylab._version import __version__

__all__ = [
    "__version__",
    "HasApp",
    "JupyterFrontEnd",
    "Connection",
    "Panel",
    "SplitPanel",
    "Icon",
    "Area",
    "InsertMode",
    "hookimpl",
    "TransformMode",
    "pack",
    "pack_code",
    "commands",
]

from ipylab.disposable_connection import Connection  # noqa: I001
from ipylab import commands
from ipylab.asyncwidget import TransformMode, pack, pack_code
from ipylab.hasapp import HasApp
from ipylab.hookspecs import hookimpl
from ipylab.jupyterfrontend import JupyterFrontEnd
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Icon, Panel, SplitPanel


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
