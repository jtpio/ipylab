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
def on_frontend_error(obj: AsyncWidgetBase, error: Exception, msg: dict) -> t.NoReturn | None:
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


@hookspec
def on_send_error(obj: AsyncWidgetBase, error: Exception, content: dict, buffers) -> None:
    """This is called when a send exception occurrs."""


@hookspec(firstresult=True)
def on_frontend_operation_error(obj: AsyncWidgetBase, error: Exception, content: dict):
    """Handle an error processing an operation from the frontend."""


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


@hookspec(firstresult=True)
def unhandled_frontend_operation_message(obj: AsyncWidgetBase, operation: str):
    """Handle a message from the frontend."""
