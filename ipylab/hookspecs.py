# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import typing as t

import pluggy

hookimpl = pluggy.HookimplMarker("ipylab")
hookspec = pluggy.HookspecMarker("ipylab")
pm = pluggy.PluginManager("ipylab")
if t.TYPE_CHECKING:
    from ipylab.asyncwidget import AsyncWidgetBase


class IpylabHookspec:
    @hookspec
    def on_frontend_error(
        self, obj: AsyncWidgetBase, error: Exception, content: dict
    ) -> t.NoReturn | None:
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

    @hookspec
    def on_send_error(self, obj: AsyncWidgetBase, error: Exception, content: dict, buffers) -> None:
        """This is called when a send exception occurs."""

    @hookspec(firstresult=True)
    def on_frontend_operation_error(self, obj: AsyncWidgetBase, error: Exception, content: dict):
        """Handle an error processing an operation from the frontend."""

    @hookspec(firstresult=True)
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        """Handle a message from the frontend."""


class IpylabDefaultsPlugin:
    @hookimpl
    def unhandled_frontend_operation_message(self, obj: AsyncWidgetBase, operation: str):
        raise RuntimeError(f"Unhandled frontend_operation_message from {obj=} {operation=}")


pm.add_hookspecs(IpylabHookspec)
pm.register(IpylabDefaultsPlugin())


def before(hook_name, hook_impls, kwargs):
    pass


def after(outcome, hook_name, hook_impls, kwargs):
    pass


stop_trace = pm.add_hookcall_monitoring(before, after)
