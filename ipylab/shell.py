# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING

from ipylab import Area, ShellConnection, Transform, pack
from ipylab.asyncwidget import AsyncWidgetBase, Unicode
from ipylab.common import InsertMode
from ipylab.connection import Connection

if TYPE_CHECKING:
    from asyncio import Task

    from ipywidgets import Widget


__all__ = ["Shell"]


class Shell(AsyncWidgetBase):
    """
    Provides access to the shell.
    The minimal interface is:
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html

    Likely the full labShell interface.

    ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add
    """

    SINGLETON = True
    _basename = Unicode("shell").tag(sync=True)

    def add(
        self,
        widget: Widget,
        *,
        area: Area = Area.main,
        activate: bool = True,
        mode: InsertMode = InsertMode.tab_after,
        rank: int | None = None,
        ref: ShellConnection | None = None,
        **options,
    ) -> Task[ShellConnection]:
        """
        Add the widget to the shell.

        ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add

        options: dict
            mode: InsertMode
            https://jupyterlab.readthedocs.io/en/latest/api/interfaces/docregistry.DocumentRegistry.IOpenOptions.html
        """
        options_ = {
            "activate": activate,
            "mode": InsertMode(mode),
            "rank": int(rank) if rank else None,
            "ref": ref.id if ref else None,
        }
        cid = ShellConnection.to_cid(widget.id if isinstance(widget, Connection) else pack(widget))

        async def add_to_shell():
            # kernelId should always be available when running as a task.
            if not self.kernelId:
                msg = "kernelId has not been set yet"
                raise RuntimeError(msg)
            return await self.execute_command(
                "ipylab:add-to-shell",
                transform={
                    "transform": Transform.connection,
                    "cid": cid,
                    "auto_dispose": not isinstance(widget, ShellConnection),
                },
                cid=cid,
                kernelId=self.kernelId,
                area=area,
                options=options_ | options,
            )

        return self.to_task(add_to_shell())

    def expand_left(self):
        return self.execute_method("expandLeft")

    def expand_right(self):
        return self.execute_method("expandRight")

    def collapse_left(self):
        return self.execute_method("collapseLeft")

    def collapse_right(self):
        return self.execute_method("collapseRight")
