# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
from typing import NotRequired, Self, TypedDict

from traitlets import Dict, Instance, Tuple, Unicode

from ipylab._plugin_manger import pm
from ipylab.asyncwidget import AsyncWidgetBase, register, widget_serialization
from ipylab.commands import CommandPalette, CommandRegistry
from ipylab.dialog import Dialog, FileDialog
from ipylab.sessions import SessionManager
from ipylab.shell import Shell


class LauncherOptions(TypedDict):
    name: str
    entry_point: str
    tooltip: NotRequired[str]
    icon: NotRequired[str]


@register
class JupyterFrontEnd(AsyncWidgetBase):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    SINGLETON = True

    version = Unicode(read_only=True).tag(sync=True)
    commands = Instance(CommandRegistry, (), read_only=True).tag(sync=True, **widget_serialization)
    command_pallet = Instance(CommandPalette, (), read_only=True).tag(
        sync=True, **widget_serialization
    )

    current_widget_id = Unicode(read_only=True).tag(sync=True)
    current_session = Dict(read_only=True).tag(sync=True)
    all_sessions = Tuple(read_only=True).tag(sync=True)

    @property
    def dialog(self) -> Dialog:
        if not hasattr(self, "_dialog"):
            self._dialog = Dialog()
        return self._dialog

    @property
    def file_dialog(self) -> FileDialog:
        if not hasattr(self, "_fileDialog"):
            self._fileDialog = FileDialog()
        return self._fileDialog

    @property
    def shell(self) -> Shell:
        if not hasattr(self, "_shell"):
            self._shell = Shell()
        return self._shell

    @property
    def sessionManager(self) -> SessionManager:
        if not hasattr(self, "_sessionManger"):
            self._sessionManger = SessionManager()
        return self._sessionManger

    async def wait_ready(self, timeout=5) -> Self:
        """Wait until connected to app indicates it is ready."""
        if not self._ready_response.is_set():
            async with asyncio.TaskGroup() as group, asyncio.timeout(timeout):
                group.create_task(super().wait_ready())
                group.create_task(self.commands.wait_ready())
                group.create_task(self.command_pallet.wait_ready())
        return self

    def _init_python_backend(self) -> str:
        "Run by the Ipylab python backend"
        # This is called in a separate kernel started by the JavaScript frontend
        # the first time the ipylab plugin is activated.
        pm.hook.register_launcher.call_historic(result_callback=self.create_launcher)
        return "done"

    def create_launcher(self, options: LauncherOptions) -> asyncio.Task:
        """Create a new launcher in Jupypterlab.

        ``` python

        @ipylab.hookimpl(specname="register_launcher")
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
        return self.schedule_operation("createLauncher", **options)
