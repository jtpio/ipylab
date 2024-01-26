# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import enum
import typing as t

import ipywidgets as ipw

from ipylab import pack
from ipylab.sub import SubApp

if t.TYPE_CHECKING:
    from ipywidgets import Widget


__all__ = ["Area", "InsertMode", "Shell"]


class Area(enum.StrEnum):
    # https://github.com/jupyterlab/jupyterlab/blob/da8e7bda5eebd22319f59e5abbaaa9917872a7e8/packages/application/src/shell.ts#L500
    main = "main"
    left = "left"
    right = "right"
    header = "header"
    top = "top"
    bottom = ("bottom",)
    down = ("down",)
    menu = "menu"


class InsertMode(enum.StrEnum):
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


class Shell(SubApp):
    """
    Provides access to the shell.
    The minimal interface is:
    https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html

    Likely the full labShell interface.

    ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add
    """

    SUBPATH = "shell"

    def addToShell(
        self,
        widget: Widget,
        area: Area,
        activate: bool = True,
        mode: InsertMode = InsertMode.split_right,
        rank: int | None = None,
        ref: ipw.Widget | None = None,
        **options,
    ) -> asyncio.Task:
        """
        Add the widget to the shell.

        ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add

        options: dict
            mode: InsertMode
            https://jupyterlab.readthedocs.io/en/latest/api/interfaces/docregistry.DocumentRegistry.IOpenOptions.html
        """

        return self.app.schedule_operation(
            "addToShell",
            serializedWidget=pack(widget),
            area=area,
            options={
                "activate": activate,
                "mode": mode,
                "rank": int(rank) if rank else None,
                "ref": pack(ref),
            }
            | options,
        )

    def expandLeft(self) -> asyncio.Task:
        return self.execute_method("expandLeft")

    def expandRight(self) -> asyncio.Task:
        return self.execute_method("expandRight")

    def collapseLeft(self) -> asyncio.Task:
        return self.execute_method("collapseLeft")

    def collapseRight(self) -> asyncio.Task:
        return self.execute_method("collapseRight")
