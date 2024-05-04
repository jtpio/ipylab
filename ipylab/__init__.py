# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from ipylab._version import __version__

__all__ = [
    "__version__",
    "HasApp",
    "JupyterFrontEnd",
    "Panel",
    "SplitPanel",
    "MainArea",
    "ViewStatus",
    "Icon",
    "Area",
    "InsertMode",
    "hookimpl",
    "TransformMode",
    "pack",
]

from ipylab.asyncwidget import TransformMode, pack
from ipylab.hasapp import HasApp
from ipylab.hookspecs import hookimpl
from ipylab.jupyterfrontend import JupyterFrontEnd
from ipylab.main_area import MainArea, ViewStatus
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Icon, Panel, SplitPanel


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
