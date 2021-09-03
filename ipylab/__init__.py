#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

# import version first: https://github.com/pypa/setuptools/issues/1724#issuecomment-627241822
from ._version import __version__, version_info

import json
import os.path as osp

from .jupyterfrontend import JupyterFrontEnd
from .widgets import Panel, SplitPanel

HERE = osp.abspath(osp.dirname(__file__))

with open(osp.join(HERE, "labextension", "package.json")) as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]
