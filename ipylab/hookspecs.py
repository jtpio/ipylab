# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import typing as t

import pluggy

hookimpl = pluggy.HookimplMarker("ipylab")
hookspec = pluggy.HookspecMarker("ipylab")

if t.TYPE_CHECKING:
    from collections.abc import Awaitable

    from ipylab.asyncwidget import AsyncWidgetBase
    from ipylab.jupyterfrontend import JupyterFrontEnd


class IpylabHookspec:
    @hookspec(firstresult=True)
    def on_frontend_error(self, obj: AsyncWidgetBase, error: Exception, content: dict, buffers) -> None:
        """Intercept an error message for logging purposes.

        Fired when the task handling comms receives the error prior to raising it.

        Args: AsyncWidgetBase
            obj:
                The object from where the error.
            error: str
                The message from the JupyterFrontend.
            content:
                The content of the message accompanying the frontend error.
        """

    @hookspec(firstresult=True)
    def on_task_error(self, obj: AsyncWidgetBase, aw: Awaitable, error: Exception) -> None:
        """Intercept an error message for logging purposes.

        Fired when an exception occurs in a task started with the method `AsyncWidgetBase.to_task`.

        Args: AsyncWidgetBase
            obj:
                The object from where the error.
        """

    @hookspec(firstresult=True)
    def on_message_error(self, obj: AsyncWidgetBase, msg: str, error: Exception) -> None:
        """Intercept an error message for logging purposes.

        Fired when an exception occurs in a task started with the method `AsyncWidgetBase.to_task`.

        Args: AsyncWidgetBase
            obj:
                The object from where the error.
        """

    @hookspec(firstresult=True)
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        """Handle a message from the frontend."""
        obj.log.error("Unknown operation '%s' for %r", operation, obj)

    @hookspec()
    async def on_app_ready(self, app: JupyterFrontEnd):
        """Called when the app is ready but not in the backend."""

    @hookspec()
    async def on_backend_ready(self, app: JupyterFrontEnd):
        "Called when the backend is ready."


class IpylabDefaultsPlugin:
    @hookimpl
    def on_frontend_error(self, obj: AsyncWidgetBase, error: Exception, content: dict, buffers) -> None:  # noqa: ARG002
        msg = obj.log.error("An error occurred on the frontend with message %s %s", error, content)
        raise RuntimeError(msg)

    @hookimpl
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        msg = f"Unhandled frontend_operation_message from {obj=} {operation=}"
        raise RuntimeError(msg)

    @hookimpl
    def on_task_error(self, obj: AsyncWidgetBase, aw: str, error: Exception) -> None:
        obj.log.error("Error executing %s", aw, exc_info=error)

    @hookimpl
    def on_message_error(self, obj: AsyncWidgetBase, msg: str, error: Exception) -> None:
        obj.log.exception("%r handling message %s", error, msg, exc_info=error)

    @hookimpl(specname="on_backend_ready")
    async def autostart_example(self, app: JupyterFrontEnd):
        "Demonstrates how to use on_backend_ready"


def get_plugin_manager():
    pm = pluggy.PluginManager("ipylab")
    pm.add_hookspecs(IpylabHookspec)
    pm.load_setuptools_entrypoints("ipylab")
    pm.register(IpylabDefaultsPlugin())
    return pm
