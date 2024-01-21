# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from ipylab.labapp import IPLabApp


def init_ipylab_backend() -> str:
    """Initialize an ipylab backend.

    Intended to run inside a kenrnel launched by Jupyter.
    """
    from ipylab.jupyterfrontend import JupyterFrontEnd

    app = JupyterFrontEnd()
    app._create_launchers()
    return "done"


def launch_jupyterlab():
    from ipylab._plugin_manger import pm

    cls: IPLabApp = pm.hook.get_ipylab_backend_class()
    cls.launch_instance()
