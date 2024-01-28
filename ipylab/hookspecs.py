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
def on_frontend_error(obj: AsyncWidgetBase, error: Exception, content: dict) -> t.NoReturn | None:
    """Intercept an error message for logging purposes.

    Fired when the task handling comms recieves the error prior to raising it.

    Args: AsyncWidgetBase
        obj:
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        content:
            The content of the message acompanying the frontend error.
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
def run_once_at_startup():
    """The function will run once when Ipylab is activated (requires entry point as explained below).

    ``` python

    @ipylab.hookimpl(specname="automatic_start")
    def plugin_my_launcher() -> LauncherOptions:
        options = LauncherOptions(name="Launch my app",
        tooltip="My app is great...",
        entry_point='my_module.my_attr.start_my_app')
        return options
    ```

    Note: The package should be installed (re-installed) with the entry point "ipylab-python-backend"

    in pyproject.toml
    ``` toml
    [project.entry-points.ipylab-python-backend]
    my_plugins = "my_module.ipylab_backend_plugin"
    ```

    entry_point: str <package_or_module>[:<object>[.<attr>[.<nested-attr>]*]]
        The script called
        Uses the same convention as setup tools.

        https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-syntax

    """


@hookspec(firstresult=True)
def unhandled_frontend_operation_message(obj: AsyncWidgetBase, operation: str):
    """Handle a message from the frontend."""
