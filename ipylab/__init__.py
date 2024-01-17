# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ._version import __version__  # noqa: F401

from ipylab.jupyterfrontend import JupyterFrontEnd
from ipylab.widgets import Panel, SplitPanel, Icon
from ipylab.shell import Area, InsertMode

__all__ = ["JupyterFrontEnd", "Panel", "SplitPanel", "Icon", "Area", "InsertMode"]


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
