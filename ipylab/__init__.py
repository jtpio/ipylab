# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ._version import __version__  # noqa: F401

__all__ = [
    "__version__",
    "JupyterFrontEnd",
    "Panel",
    "SplitPanel",
    "MainArea",
    "Icon",
    "Area",
    "InsertMode",
    "hookimpl",
    "hookspecs",
    "LauncherOptions",
]

import pluggy

hookimpl = pluggy.HookimplMarker("ipylab")
"""Marker to be imported and used in plugins (and for own implementations)"""

from ipylab.jupyterfrontend import JupyterFrontEnd, LauncherOptions
from ipylab.main_area import MainArea
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Icon, Panel, SplitPanel


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
