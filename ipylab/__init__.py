#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import json
from pathlib import Path

from ._version import __version__

from .jupyterfrontend import JupyterFrontEnd
from .widgets import Panel, SplitPanel, Icon
from .icon import Icon

HERE = Path(__file__).parent.resolve()

with open(str(HERE / "labextension" / "package.json")) as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]
