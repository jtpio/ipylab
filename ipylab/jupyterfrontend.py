# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
from typing import Callable, Self

from traitlets import Instance, Unicode

import ipylab
from ipylab._plugin_manger import pm
from ipylab.asyncwidget import AsyncWidgetBase, register, widget_serialization
from ipylab.commands import CommandPalette, CommandRegistry
from ipylab.dialog import Dialog
from ipylab.sessions import SessionManager
from ipylab.shell import Shell


@register
class JupyterFrontEnd(AsyncWidgetBase):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    SINGLETON = True

    version = Unicode(read_only=True).tag(sync=True)
    shell = Instance(Shell, (), read_only=True).tag(sync=True, **widget_serialization)
    commands = Instance(CommandRegistry, (), read_only=True).tag(sync=True, **widget_serialization)
    sessions = Instance(SessionManager, (), read_only=True).tag(sync=True, **widget_serialization)
    command_pallet = Instance(CommandPalette, (), read_only=True).tag(
        sync=True, **widget_serialization
    )

    @property
    def dialog(self) -> Dialog:
        if not hasattr(self, "_dialog"):
            self._dialog = Dialog(self)
        return self._dialog

    async def wait_ready(self, timeout=5) -> Self:
        """Wait until connected to app indicates it is ready."""
        if not self._ready_response.is_set():
            async with asyncio.TaskGroup() as group, asyncio.timeout(timeout):
                group.create_task(super().wait_ready())
                group.create_task(self.shell.wait_ready())
                group.create_task(self.commands.wait_ready())
                group.create_task(self.command_pallet.wait_ready())
                group.create_task(self.sessions.wait_ready())
        return self

    def _create_launchers(self):
        "Run by the Ipylab python backend"
        pm.hook.register_launcher(callback=self.create_launcher)

    def create_launcher(self, name: str, tooltip: str, icon: str, entry_point: str) -> asyncio.Task:
        """Create a new launcher in jupyter.

        Normally this would be done by registering the plugin.

        ``` python

        @ipylab.hookimpl
        def register_launcher(callback):
            callback(name="Launch my app",
            tooltip="My app is great...",
            entry_point='my_module.my_attr.start_my_app')
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
        return self.schedule_operation(
            "createLauncher", name=name, tooltip=tooltip, icon=icon, entry_point=entry_point
        )

    def open_console(self, session: dict | None = None, **kwgs) -> asyncio.Task:
        if session is None:
            session = self.sessions.app_session
        return self.commands.execute("console:open", **session | kwgs)
