# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from traitlets import Callable as CallableTrait
from traitlets import Tuple, Unicode

from ipylab._compat.typing import Any, Optional, TypedDict, Unpack
from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack, register
from ipylab.disposable_connection import DisposableConnection
from ipylab.jupyterfrontend_subsection import FrontEndSubsection

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Callable, Coroutine

    from ipylab.widgets import Icon


class CommandOptions(TypedDict):
    enabled: Optional[bool]
    visible: Optional[bool]
    toggled: Optional[bool]


class CommandConnection(DisposableConnection):
    """A Disposable Ipylab command registered in the command pallet."""

    ID_PREFIX = "ipylab_command"
    python_command = CallableTrait(allow_none=False)

    def configure(self, *, emit=True, **kwgs: Unpack[CommandOptions]) -> Task[CommandOptions]:
        async def configure_():
            config = await self.get_config()
            for k, v in kwgs.items():
                if v is not None:
                    config[k] = v
            await self.set_attribute("config", config)
            if emit:
                await self.app.commands.execute_method("commandChanged.emit", {"id": self.id})
            return config

        return self.to_task(configure_())

    def get_config(self) -> Task[CommandOptions]:
        async def get_config_():
            config = await self.get_attribute("config", ifMissing="null")
            return config or {}

        return self.to_task(get_config_())


@register
class CommandPalette(AsyncWidgetBase):
    _model_name = Unicode("CommandPaletteModel").tag(sync=True)
    items = Tuple(read_only=True).tag(sync=True)

    def add_item(self, command_id: str | CommandConnection, category: str, *, rank=None, args: dict | None = None):
        return self.schedule_operation(
            operation="addItem",
            id=str(command_id),
            category=category,
            rank=rank,
            args=args,
            transform=TransformMode.connection,
        )

    def remove_item(self, command_id: str | CommandConnection, category):
        return self.schedule_operation(operation="removeItem", id=str(command_id), category=category)


@register
class Launcher(CommandPalette):
    _model_name = Unicode("LauncherModel").tag(sync=True)


@register
class CommandRegistry(FrontEndSubsection):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    SINGLETON = True
    SUB_PATH_BASE = "app.commands"
    all_commands = Tuple(read_only=True).tag(sync=True)

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "execute":
                conn = self.get_existing_command_connection(payload["id"])
                if not conn:
                    msg = f"Command not found with id='{payload['id']}'!"
                    raise RuntimeError(msg)
                cmd = conn.python_command
                kwgs = payload.get("kwgs") or {} | {"buffers": buffers}
                for k in set(kwgs).difference(inspect.signature(cmd).parameters.keys()):
                    kwgs.pop(k)
                result = cmd(**kwgs)
                if inspect.isawaitable(result):
                    return await result
                return result
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def add_command(
        self,
        name: str,
        execute: Callable[..., Coroutine | Any],
        *,
        caption="",
        label="",
        icon_class="",
        icon: Icon | None = None,
        command_result_transform: TransformMode = TransformMode.done,
        **kwgs,
    ) -> Task[CommandConnection]:
        """Add a python command that can be executed by Jupyterlab.

        name: str
            The suffix for the 'id'.
        execute:

        kwgs:
            Additional ICommandOptions can be passed as kwgs

        ref: https://lumino.readthedocs.io/en/latest/api/interfaces/commands.CommandRegistry.ICommandOptions.html
        """
        task = self.schedule_operation(
            "add_command",
            id=CommandConnection.to_id(name),
            caption=caption,
            label=label,
            iconClass=icon_class,
            transform=TransformMode.connection,
            icon=pack(icon),
            command_result_transform=command_result_transform,
            **kwgs,
        )

        async def add_command_():
            conn: CommandConnection = await task
            conn.set_trait("python_command", execute)
            return conn

        return self.to_task(add_command_())

    def remove_command(self, name_or_id: str):
        comm = self.get_existing_command_connection(name_or_id)
        if comm:
            comm.dispose()

    def get_existing_command_connection(self, name_or_id: str) -> CommandConnection | None:
        "Will return a CommandConnection if it was added in this kernel."
        return CommandConnection.get_existing_connection(name_or_id)
