# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import typing as t

from ipylab import pack
from ipylab._compat.enum import StrEnum
from ipylab.asyncwidget import AsyncWidgetBase, TransformMode, Unicode
from ipylab.disposable_connection import DisposableConnection

if t.TYPE_CHECKING:
    from asyncio import Task

    from ipywidgets import Widget

__all__ = ["Area", "InsertMode", "Shell"]


class Area(StrEnum):
    # https://github.com/jupyterlab/jupyterlab/blob/da8e7bda5eebd22319f59e5abbaaa9917872a7e8/packages/application/src/shell.ts#L500
    main = "main"
    left = "left"
    right = "right"
    header = "header"
    top = "top"
    bottom = "bottom"
    down = "down"
    menu = "menu"


class InsertMode(StrEnum):
    # ref https://lumino.readthedocs.io/en/latest/api/types/widgets.DockLayout.InsertMode.html
    split_top = "split-top"
    split_left = "split-left"
    split_right = "split-right"
    split_bottom = "split-bottom"
    merge_top = "merge-top"
    merge_left = "merge-left"
    merge_right = "merge-right"
    merge_bottom = "merge-bottom"
    tab_before = "tab-before"
    tab_after = "tab-after"


class Shell(AsyncWidgetBase):
    """
    Provides access to the shell.
    The minimal interface is:
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html

    Likely the full labShell interface.

    ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add
    """

    _basename = Unicode("shell").tag(sync=True)

    def addToShell(
        self,
        widget: Widget,
        *,
        area: Area = Area.main,
        activate: bool = True,
        mode: InsertMode = InsertMode.split_right,
        rank: int | None = None,
        ref: DisposableConnection | str = "",
        **options,
    ) -> Task[DisposableConnection]:
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
            "ref": ref.id if isinstance(ref, DisposableConnection) else ref or None,
        }
        return self.app.schedule_operation(
            "addToShell",
            widget=pack(widget),
            area=Area(area),
            transform=TransformMode.connection,
            options=options_ | options,
            toLuminoWidget=["widget", "options.ref"],
        )

    def expandLeft(self):
        return self.execute_method("expandLeft")

    def expandRight(self):
        return self.execute_method("expandRight")

    def collapseLeft(self):
        return self.execute_method("collapseLeft")

    def collapseRight(self):
        return self.execute_method("collapseRight")
