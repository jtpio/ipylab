# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import sys


def init_ipylab_backend():
    """Initialize an ipylab backend.

    Intended to run inside a kernel launched by Jupyter.
    """
    from ipylab.jupyterfrontend import JupyterFrontEnd

    app = JupyterFrontEnd()
    return app._init_python_backend()  # noqa: SLF001


def launch_jupyterlab():
    from ipylab.labapp import IPLabApp

    sys.exit(IPLabApp.launch_instance())
