# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import enum
import typing as t
from traitlets import List, Unicode
import ipywidgets as ipw
from .asyncwidget import AsyncWidgetBase, register, widget_serialization

if t.TYPE_CHECKING:
    from ipywidgets import Widget


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


@register
class Shell(AsyncWidgetBase):
    _model_name = Unicode("ShellModel").tag(sync=True)
    _widgets = List([], read_only=True).tag(sync=True)
    SINGLETON = True

    def add(
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
        add the widget to the shell.

        ref: https://jupyterlab.readthedocs.io/en/latest/api/interfaces/application.JupyterFrontEnd.IShell.html#add

        options: dict
            mode: InsertMode
            https://jupyterlab.readthedocs.io/en/latest/api/interfaces/docregistry.DocumentRegistry.IOpenOptions.html
        """

        return self.schedule_operation(
            "add",
            serializedWidget=widget_serialization["to_json"](widget, None),
            area=area,
            options={
                "activate": activate,
                "mode": mode,
                "rank": int(rank) if rank else None,
                "ref": None or widget_serialization["to_json"](ref, None),
            }
            | options,
        )

    def expand_left(self) -> asyncio.Task:
        return self.schedule_operation("expandLeft")

    def expand_right(self) -> asyncio.Task:
        return self.schedule_operation("expandRight")

    def collapse_left(self) -> asyncio.Task:
        return self.schedule_operation("collapseLeft")

    def collapse_right(self) -> asyncio.Task:
        return self.schedule_operation("collapseRight")
