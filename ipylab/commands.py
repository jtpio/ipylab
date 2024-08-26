# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from ipywidgets import TypedTuple
from traitlets import Callable as CallableTrait
from traitlets import Container, Instance, Tuple, Unicode, observe

from ipylab._compat.typing import Any, Optional, TypedDict, Unpack
from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, pack, register
from ipylab.disposable_connection import DisposableConnection

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

    ID_PREFIX = "ipylab command"
    python_command = CallableTrait(allow_none=False)

    @observe("comm")
    def _ipylab_observe_comm(self, _):
        self.app.commands.set_trait("items", self.get_instances())

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
            config = await self.get_attribute("config", nullIfMissing=True)
            return config or {}

        return self.to_task(get_config_())

    def add_launcher(self, category: str):
        """Add a launcher for this command.

        When this link is closed the launcher will be disposed.
        """

        async def add_launcher_():
            launcher = await self.app.commands.launcher.add(self, category)
            self.observe(lambda _: launcher.dispose(), names="comm")
            return launcher

        return self.to_task(add_launcher_())

    def add_to_command_pallet(self, category: str):
        """Add a pallet item for this command.

        When this link is closed the pallet item will be disposed.
        """

        async def add_to_command_pallet_():
            pallet_item = await self.app.commands.pallet.add(self, category)
            self.observe(lambda _: pallet_item.dispose(), names="comm")
            return pallet_item

        return self.to_task(add_to_command_pallet_())


class CommandPalletConnection(DisposableConnection):
    """
    ref:
    """

    ID_PREFIX = "ipylab command pallet"

    @observe("comm")
    def _ipylab_observe_comm(self, _):
        self.app.commands.pallet.set_trait("items", self.get_instances())


class LauncherConnection(DisposableConnection):
    """
    ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/launcher.ILauncher-1.html
    """

    ID_PREFIX = "ipylab launcher"

    @observe("comm")
    def _ipylab_observe_comm(self, _):
        self.app.commands.launcher.set_trait("items", self.get_instances())


class CommandPalette(AsyncWidgetBase):
    _basename = Unicode("pallet").tag(sync=True)
    SINGLETON = True
    items: Container[tuple[CommandPalletConnection, ...]] = TypedTuple(trait=Instance(CommandPalletConnection))

    def _to_pallet_command_category_id(self, command_id: str | CommandConnection, category: str):
        cmd = str(CommandConnection.get_existing_connection(command_id))
        return f"{CommandPalletConnection.to_id(str(cmd))} | {category}"

    def add(
        self,
        command: str | CommandConnection,
        category: str,
        *,
        rank=None,
        kernelIconUrl="",
        metadata: dict | None = None,
        **args,
    ) -> Task[CommandPalletConnection]:
        """Add a command to the command pallet (must be registered in this kerenel)."""
        id_ = self._to_pallet_command_category_id(command, category)
        conn = CommandPalletConnection.get_existing_connection(id_, quiet=True)
        if conn:
            conn.dispose()
        return self.execute_method(
            "addItem",
            {
                "command": str(command),
                "category": category,
                "rank": rank,
                "args": args,
                "kernelIconUrl": kernelIconUrl,
                "metadata": metadata,
            },
            id=id_,
            transform=TransformMode.connection,
        )

    def remove(self, command_id: str | CommandConnection, category: str):
        conn = CommandPalletConnection.get_existing_connection(
            self._to_pallet_command_category_id(command_id, category), quiet=True
        )
        if conn:
            conn.dispose()


class Launcher(AsyncWidgetBase):
    _basename = Unicode("launcher").tag(sync=True)
    SINGLETON = True
    items: Container[tuple[LauncherConnection, ...]] = TypedTuple(trait=Instance(LauncherConnection))

    def _to_launcher_connection_id(self, command_id: str | CommandConnection, category: str):
        cmd = str(CommandConnection.get_existing_connection(command_id))
        return f"{LauncherConnection.to_id(str(cmd))} | {category}"

    def add(self, command: str | CommandConnection, category: str, *, rank=None, **args) -> Task[LauncherConnection]:
        """Add a launcher for the command (must be registered in this kerenel).

        ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/launcher.ILauncher.IItemOptions.html
        """
        id_ = self._to_launcher_connection_id(command, category)
        conn = LauncherConnection.get_existing_connection(id_, quiet=True)
        if conn:
            conn.dispose()
        return self.execute_method(
            "add",
            {
                "command": str(command),
                "category": category,
                "rank": rank,
                "args": args,
            },
            id=id_,
            transform=TransformMode.connection,
        )

    def remove(self, command_id: str | CommandConnection, category: str):
        conn = LauncherConnection.get_existing_connection(self._to_launcher_connection_id(command_id, category))
        if conn:
            conn.dispose()


@register
class CommandRegistry(AsyncWidgetBase):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    SINGLETON = True
    all_commands = Tuple(read_only=True).tag(sync=True)
    pallet = Instance(CommandPalette, (), read_only=True)
    launcher = Instance(Launcher, (), read_only=True)

    items: Container[tuple[CommandConnection, ...]] = TypedTuple(trait=Instance(CommandConnection))

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "execute":
                conn = self.get_existing_command_connection(payload["id"])
                cmd = conn.python_command
                kwgs = payload.get("kwgs") or {} | {"buffers": buffers}
                for k in set(kwgs).difference(inspect.signature(cmd).parameters.keys()):
                    kwgs.pop(k)
                result = cmd(**kwgs)
                if inspect.isawaitable(result):
                    return await result
                return result
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def add(
        self,
        name: str,
        execute: Callable[..., Coroutine | Any],
        *,
        caption="",
        label="",
        icon_class="",
        icon: Icon | None = None,
        commandResultTransform: TransformMode | dict[str, Any] = TransformMode.done,
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
            "addCommand",
            id=CommandConnection.to_id(name),
            caption=caption,
            label=label,
            iconClass=icon_class,
            transform=TransformMode.connection,
            icon=pack(icon),
            commandResultTransform=commandResultTransform,
            **kwgs,
        )

        async def add_command_():
            conn: CommandConnection = await task
            conn.set_trait("python_command", execute)
            return conn

        return self.to_task(add_command_())

    def remove_command(self, name_or_id: str):
        conn = self.get_existing_command_connection(name_or_id)
        if conn:
            conn.dispose()

    def get_existing_command_connection(self, name_or_id: str) -> CommandConnection:
        "Will return a CommandConnection if it was added in this kernel."
        return CommandConnection.get_existing_connection(name_or_id)  # type: ignore
