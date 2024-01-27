# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio
from typing import Callable

from traitlets import Dict, Tuple, Unicode, observe

from ipylab._plugin_manger import pm
from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack, register
from ipylab.widgets import Icon


@register
class CommandPalette(AsyncWidgetBase):
    _model_name = Unicode("CommandPaletteModel").tag(sync=True)

    items = Tuple(read_only=True).tag(sync=True)

    def add_item(
        self, command_id: str, category, *, rank=None, args: dict | None = None, **kwgs
    ) -> asyncio.Task:
        return self.schedule_operation(
            operation="addItem",
            id=command_id,
            category=category,
            rank=rank,
            args=args,
            **kwgs,
        )

    def remove_item(self, command_id: str, category) -> asyncio.Task:
        return self.schedule_operation(operation="addItem", id=command_id, category=category)


@register
class CommandRegistry(AsyncWidgetBase):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    SINGLETON = True
    commands = Tuple(read_only=True).tag(sync=True)

    _execute_callbacks: dict[str : Callable[[], None]] = Dict()

    @observe("commands")
    def _observe_commands(self, change):
        commands = self.commands
        for k in tuple(self._execute_callbacks):
            if k not in commands:
                self._execute_callbacks.pop(k)

    async def _do_operation_for_frontend(
        self, operation: str, payload: dict, buffers: list
    ) -> bool | None:
        match operation:
            case "execute":
                command_id = payload.get("id")
                cmd = self._execute_callbacks[command_id]
                result = cmd(**payload.get("kwgs", {}))
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            case _:
                pm.hook.unhandled_frontend_operation_message(self, operation)

    def execute(
        self,
        command_id: str,
        transform: TransformMode | dict[str, str] = TransformMode.done,
        **args,
    ) -> asyncio.Task:
        """Execute command_id.

        `args` correspond to `args` in JupyterLab.

        Finding what the `args` are remains an outstanding issue in JupyterLab.

        see: https://github.com/jtpio/ipylab/issues/128#issuecomment-1683097383 for hints
        about how args can be found.
        """
        return self.execute_method("app.commands.execute", command_id, args, transform=transform)

    def addPythonCommand(
        self,
        command_id: str,
        execute: Callable,
        *,
        caption="",
        label="",
        icon_class="",
        icon: Icon = None,
        **kwgs,
    ):
        if command_id in self.commands:
            raise Exception(f"Command '{command_id} is already registered!")
        # TODO: support other parameters (isEnabled, isVisible...)
        self._execute_callbacks = self._execute_callbacks | {command_id: execute}
        return self.schedule_operation(
            "addPythonCommand",
            id=command_id,
            caption=caption,
            label=label,
            iconClass=icon_class,
            icon=pack(icon),
            **kwgs,
        )

    def remove_command(self, command_id: str, **kwgs) -> asyncio.Task:
        # TODO: check whether to keep this method, or return disposables like in lab
        if command_id not in self.commands:
            raise ValueError(f"{command_id=} is not a registered command!")
        return self.schedule_operation("removePythonCommand", command_id=command_id, **kwgs)
