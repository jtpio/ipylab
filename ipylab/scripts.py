# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import sys


def launch_jupyterlab():
    from ipylab.labapp import IPLabApp

    sys.exit(IPLabApp.launch_instance())
