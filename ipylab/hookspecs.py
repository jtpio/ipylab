# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import typing as t

import pluggy

hookspec = pluggy.HookspecMarker("ipylab")

if t.TYPE_CHECKING:
    from collections.abc import Awaitable

    from ipylab import Ipylab
    from ipylab.jupyterfrontend import JupyterFrontEnd


class IpylabHookspec:
    @hookspec()
    async def autostart(self, app: JupyterFrontEnd):
        """
        Called inside each Python kernel when the frontend is 'ready'.

        Use this with modules that define entry points.

        To run in the Ipylab kernel exclusively use.

        ``` python
        if not app.is_ipylab_kernel:
            return
        ```
        """

    @hookspec(firstresult=True)
    def on_frontend_error(self, obj: Ipylab, error: Exception, content: dict, buffers) -> None:
        """
        Called with details of an error that occurred in the frontend.

        Fired when the task handling comms receives the error prior to raising it.

        Args
        ----

        obj: Ipylab
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        content:
            The content of the message accompanying the frontend error.
        """

    @hookspec(firstresult=True)
    def on_do_operation_for_fe_error(self, obj: Ipylab, error: Exception, content: dict, buffers) -> None:
        """
        Called when an exception occurs when performing an operation request for the frontend.

        Fired when the task handling comms receives the error prior to raising it.

        Args
        ----

        obj: Ipylab
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        content:
            The content of the message accompanying the frontend error.
        """

    @hookspec(firstresult=True)
    def on_send_error(self, obj: Ipylab, error: Exception, content: dict, buffers) -> None:
        """
        Handle a send error message for logging purposes.

        Fired when the task handling comms receives the error prior to raising it.

        Args
        ----

        obj: Ipylab
            The object from where the error.
        error: str
            The message from the JupyterFrontend.
        content:
            The content of the message accompanying the frontend error.
        """

    @hookspec(firstresult=True)
    def on_task_error(self, obj: Ipylab, aw: Awaitable, error: Exception) -> None:
        """
        Fired when an exception occurs in a task started with the method `Ipylab.to_task`.

        Args
        ----

        obj: Ipylab
            The object from where the error.

        aw: Awaitable
            The awaitable object running in the task.

        error: Exception
            The exception.
        """

    @hookspec(firstresult=True)
    def on_message_error(self, obj: Ipylab, msg: str, error: Exception) -> None:
        """
        Intercept an error message for logging purposes.

        Fired when an exception occurs trying to process a message from the frontend.

        Args
        ----

        obj: Ipylab
            The object from where the error.

        aw: Awaitable
            The awaitable object running in the task.

        error: Exception
            The exception.
        """
