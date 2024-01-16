# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
import asyncio
from typing import Self

from traitlets import Instance, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, register, widget_serialization
from ipylab.commands import CommandPalette, CommandRegistry
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

    async def wait_ready(self, timeout=5) -> Self:
        """Wait until connected to app indicates it is ready."""
        async with asyncio.TaskGroup() as group, asyncio.timeout(timeout):
            group.create_task(super().wait_ready())
            group.create_task(self.shell.wait_ready())
            group.create_task(self.commands.wait_ready())
            group.create_task(self.command_pallet.wait_ready())
        return self
