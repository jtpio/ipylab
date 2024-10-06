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
        """
        Intercept an error message for logging purposes.

        Fired when the task handling comms receives the error prior to raising it.

        Args
        ----

        obj: AsyncWidgetBase
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        content:
            The content of the message accompanying the frontend error.
        """

    @hookspec(firstresult=True)
    def on_task_error(self, obj: AsyncWidgetBase, aw: Awaitable, error: Exception) -> None:
        """
        Intercept an error message for logging purposes.

        Fired when an exception occurs in a task started with the method `AsyncWidgetBase.to_task`.

        Args
        ----

        obj: AsyncWidgetBase
            The object from where the error.

        aw: Awaitable
            The awaitable object running in the task.

        error: Exception
            The exception.
        """

    @hookspec(firstresult=True)
    def on_message_error(self, obj: AsyncWidgetBase, msg: str, error: Exception) -> None:
        """
        Intercept an error message for logging purposes.

        Fired when an exception occurs trying to process a message from the frontend.

        Args
        ----

        obj: AsyncWidgetBase
            The object from where the error.

        aw: Awaitable
            The awaitable object running in the task.

        error: Exception
            The exception.
        """

    @hookspec(firstresult=True)
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        """Handle a message from the frontend."""
        obj.log.error("Unknown operation '%s' for %r", operation, obj)

    @hookspec()
    async def autostart(self, app: JupyterFrontEnd):
        """
        Called inside each Python kernel when the frontend is 'ready'.

        Use this with modules that define entry points.
        """

    @hookspec()
    async def ipylab_only_autostart(self, app: JupyterFrontEnd):
        """
        Called inside the Ipylab Python kernel ONLY. Called when the frontend is 'ready'.

        Use this with modules that define entry points.
        """


class IpylabDefaultsPlugin:
    @hookimpl
    def on_frontend_error(self, obj: AsyncWidgetBase, error: Exception, content: dict, buffers) -> None:  # noqa: ARG002
        obj.log.exception("%r on_frontend_error %s", error, exc_info=error)
        import ipylab

        ipylab.app.dialog.show_error_message("Frontend error", f"{obj=} error='{error}'")

    @hookimpl
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        import ipylab

        ipylab.app.dialog.show_error_message("Unhandled frontend message", f"The {operation=} is unhandled for {obj} ")

    @hookimpl
    def on_task_error(self, obj: AsyncWidgetBase, aw: str, error: Exception) -> None:
        obj.log.exception("%r on_task_error %s aw=%s", error, aw, exc_info=error)

    @hookimpl
    def on_message_error(self, obj: AsyncWidgetBase, msg: str, error: Exception) -> None:
        """
        Called when an error occurs when processing a message from the Frontend.
        """
        obj.log.exception("%r on_message_error %s", error, msg, exc_info=error)
        import ipylab

        ipylab.app.dialog.show_error_message("Message error", f"{error=}\n{obj=}\n{msg=}'")


_plugin_manager = pluggy.PluginManager("ipylab")
_plugin_manager.add_hookspecs(IpylabHookspec)
_plugin_manager.register(IpylabDefaultsPlugin())
