#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ._version import __version__

from .jupyterfrontend import JupyterFrontEnd
from .widgets import Panel, SplitPanel, Icon
from .icon import Icon


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "ipylab"}]
