# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, ClassVar

from ipywidgets import TypedTuple
from traitlets import Callable as CallableTrait
from traitlets import Container, Instance, Tuple, Unicode, observe

from ipylab._compat.typing import Any, NotRequired, TypedDict, Unpack
from ipylab.asyncwidget import AsyncWidgetBase, Transform, pack, register
from ipylab.connection import Connection
from ipylab.widgets import Icon

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Callable, Coroutine, Iterable

    from ipylab.asyncwidget import TransformType

__all__ = ["CommandConnection", "CommandPalletConnection", "LauncherConnection"]


class CommandOptions(TypedDict):
    caption: NotRequired[str]
    className: NotRequired[str]  # noqa: N815
    dataset: NotRequired[Any]
    describedBy: NotRequired[dict]  # noqa: N815
    iconClass: NotRequired[str]  # noqa: N815
    iconLabel: NotRequired[str]  # noqa: N815
    isEnabled: NotRequired[bool]  # noqa: N815
    isToggled: NotRequired[bool]  # noqa: N815
    isVisible: NotRequired[bool]  # noqa: N815
    label: NotRequired[str]
    mnemonic: NotRequired[str]
    usage: NotRequired[str]


class CommandConnection(Connection):
    """A Disposable Ipylab command registered in the command pallet."""

    CID_PREFIX = "ipylab command"
    python_command = CallableTrait(allow_none=False)

    _config_options: ClassVar = set(CommandOptions.__annotations__)

    @observe("comm")
    def _ipylab_observe_comm(self, _):
        self.app.commands.set_trait("items", self.get_instances())

    def configure(self, *, emit=True, **kwgs: Unpack[CommandOptions]) -> Task[CommandOptions]:
        if diff := set(kwgs).difference(self._config_options):
            msg = f"The following useless configuration options were detected for {diff} in {self}"
            raise KeyError(msg)

        async def configure_():
            config = await self.update_values("config", kwgs)  # type: ignore
            if emit:
                await self.app.commands.execute_method("commandChanged.emit", {"id": self.cid})
            return config

        return self.to_task(configure_())

    def add_launcher(self, category: str, rank=None, **args):
        """Add a launcher for this command.

        **args are used when calling the command.

        When this link is closed the launcher will be disposed.
        """

        async def add_launcher_():
            launcher = await self.app.commands.launcher.add(self, category, rank=rank, **args)
            self.observe(lambda _: launcher.dispose(), names="comm")
            return launcher

        return self.to_task(add_launcher_())

    def add_to_command_pallet(self, category: str, rank=None, **args):
        """Add a pallet item for this command.

        **args are used when calling the command.

        When this link is closed the pallet item will be disposed.
        """

        async def add_to_command_pallet_():
            pallet_item = await self.app.commands.pallet.add(self, category, rank=rank, **args)
            self.observe(lambda _: pallet_item.dispose(), names="comm")
            return pallet_item

        return self.to_task(add_to_command_pallet_())


class CommandPalletConnection(Connection):
    """A connection to an ipylab command in the Jupyter command pallet."""

    CID_PREFIX = "ipylab command pallet"

    @classmethod
    def to_cid(cls, command: str | CommandConnection, category: str):
        return super().to_cid(str(command), category)

    @classmethod
    def get_existing_connection(cls, command: str | CommandConnection, category: str, *, quiet=False):
        return super().get_existing_connection(str(command), category, quiet=quiet)

    @classmethod
    def new_cid(cls, command: str | CommandConnection, category: str):
        return super().new_cid(str(command), category)


class CommandPalette(AsyncWidgetBase):
    # https://jupyterlab.readthedocs.io/en/latest/api/interfaces/apputils.ICommandPalette.html
    _basename = Unicode("pallet").tag(sync=True)
    SINGLETON = True
    items: Container[tuple[CommandPalletConnection, ...]] = TypedTuple(trait=Instance(CommandPalletConnection))

    def add(
        self, command: str | CommandConnection, category: str, *, rank=None, args: dict | None = None
    ) -> Task[CommandPalletConnection]:
        """Add a command to the command pallet (must be registered in this kernel).

        **args are used when calling the command.
        """
        conn = CommandPalletConnection.get_existing_connection(command, category, quiet=True)
        if conn:
            conn.dispose()
        info = {"args": args, "category": category, "command": str(command), "rank": rank}
        task = self.execute_method(
            "addItem",
            info,
            transform={
                "transform": Transform.connection,
                "cid": CommandPalletConnection.to_cid(str(command), category),
                "info": info,
            },
        )
        return self.to_task(self._add_to_tuple_trait("items", task))

    def remove(self, command: str | CommandConnection, category: str):
        conn = CommandPalletConnection.get_existing_connection(str(command), category, quiet=True)
        if conn:
            conn.dispose()


class LauncherConnection(CommandPalletConnection):
    """A connection to an disposable launcher item."""

    CID_PREFIX = "ipylab launcher"


class Launcher(AsyncWidgetBase):
    """
    ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/launcher.ILauncher-1.html"""

    _basename = Unicode("launcher").tag(sync=True)
    SINGLETON = True
    items: Container[tuple[LauncherConnection, ...]] = TypedTuple(trait=Instance(LauncherConnection))

    def add(self, command: str | CommandConnection, category: str, *, rank=None, **args) -> Task[LauncherConnection]:
        """Add a launcher for the command (must be registered in this kernel).

        ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/launcher.ILauncher.IItemOptions.html
        """
        conn = LauncherConnection.get_existing_connection(command, category, quiet=True)
        if conn:
            conn.dispose()
        info = {"command": str(command), "category": category, "rank": rank, "args": args}
        task = self.execute_method(
            "add",
            info,
            transform={
                "transform": Transform.connection,
                "cid": LauncherConnection.to_cid(str(command), category),
                "info": info,
            },
        )
        return self.to_task(self._add_to_tuple_trait("items", task))

    def remove(self, command_id: str | CommandConnection, category: str):
        conn = LauncherConnection.get_existing_connection(str(command_id), category)
        if conn:
            conn.dispose()


@register
class CommandRegistry(AsyncWidgetBase):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    _basename = Unicode("commands").tag(sync=True)
    all_commands = Tuple(read_only=True).tag(sync=True)
    pallet = Instance(CommandPalette, (), read_only=True)
    launcher = Instance(Launcher, (), read_only=True)
    items: Container[tuple[CommandConnection, ...]] = TypedTuple(trait=Instance(CommandConnection))

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list) -> Any:
        match operation:
            case "execute":
                conn = self.get_existing_command_connection(payload["id"])
                if not conn:
                    msg = f'Command not found: "{payload["id"]}"'
                    raise RuntimeError(msg)
                cmd = conn.python_command
                kwgs = (payload.get("args") or {}) | {"buffers": buffers}
                for k in set(kwgs).difference(inspect.signature(cmd).parameters):
                    kwgs.pop(k)
                result = cmd(**kwgs)
                if inspect.isawaitable(result):
                    return await result
                return result
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    def execute(
        self,
        command_id: str | CommandConnection,
        *,
        transform: TransformType = Transform.done,
        toLuminoWidget: Iterable[str] | None = None,
        toObject: Iterable[str] | None = None,
        **args,
    ):
        """Execute a command registered with `id` in Jupyterlab.

        `args` are passed to the command.

        execute_kwgs: dict | None
            Passed to execute_method (we use a dict to avoid any potential of argument clash).

        see: https://github.com/jtpio/ipylab/issues/128#issuecomment-1683097383 for hints
        about what args can be used.
        """
        return self.execute_method(
            "execute",
            str(command_id),
            args,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
            toObject=toObject,
        )

    def add(
        self,
        name: str,
        execute: Callable[..., Coroutine | Any],
        *,
        caption="",
        label="",
        icon_class: str | None = None,
        icon: Icon | None = None,
        frontend_transform: TransformType = Transform.done,
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
        cid = CommandConnection.to_cid(name)
        self.remove_command(cid)
        icon_, to_object = (f"{pack(icon)}.labIcon", ["icon"]) if isinstance(icon, Icon) else (icon, None)

        task = self.schedule_operation(
            "addCommand",
            id=cid,
            caption=caption,
            label=label,
            iconClass=icon_class,
            transform={"transform": Transform.connection, "cid": cid},
            icon=icon_,
            toObject=to_object,
            frontendTransform=Transform.validate(frontend_transform),
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

    def get_existing_command_connection(self, name_or_id: str) -> CommandConnection | None:
        "Will return a CommandConnection if it was added in this kernel."
        return CommandConnection.get_existing_connection(name_or_id, quiet=True)
