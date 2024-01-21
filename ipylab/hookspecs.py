# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import typing as t

import pluggy

hookspec = pluggy.HookspecMarker("ipylab")

if t.TYPE_CHECKING:
    import jupyterlab.labapp

    from ipylab.asyncwidget import AsyncWidgetBase


@hookspec
def on_frontend_error(obj: AsyncWidgetBase, error: str, msg: dict) -> t.NoReturn | None:
    """Intercept an error message for logging purposes.

    Fired when the task handling comms recieves the error prior to raising it.

    Args: AsyncWidgetBase
        obj:
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        msg:
            The message that was sent that corresponds to the frontend error.
    """


@hookspec(firstresult=True)
def get_ipylab_backend_class() -> type[jupyterlab.labapp.LabApp]:
    """Return the class to use as the backend.

    This will override the app used when launching with the console command `ipylab ...`.
    or when calling `python -m ipylab ...`
    """


@hookspec(historic=True)
def register_launcher(callback: t.Callable[[dict], None]):
    """Register a Jupyterlab launcher.

    see app._create_launcher for the required arguments.
    """
