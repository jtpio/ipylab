# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ipywidgets import Box, DOMWidget, register, widget_serialization
from ipywidgets.widgets.trait_types import InstanceDict
from traitlets import Dict, Instance, Unicode, observe

import ipylab._frontend as _fe
from ipylab.asyncwidget import WidgetBase
from ipylab.hasapp import HasApp
from ipylab.shell import Area, InsertMode

if TYPE_CHECKING:
    from asyncio import Task

    from ipylab.disposable_connection import DisposableConnection


@register
class Icon(DOMWidget, WidgetBase):
    _model_name = Unicode("IconModel").tag(sync=True)
    _view_name = Unicode("IconView").tag(sync=True)

    name = Unicode().tag(sync=True)
    svgstr = Unicode().tag(sync=True)


@register
class Title(WidgetBase):
    _model_name = Unicode("TitleModel").tag(sync=True)

    label = Unicode().tag(sync=True)
    icon_class = Unicode().tag(sync=True)
    caption = Unicode().tag(sync=True)
    class_name = Unicode().tag(sync=True)
    dataset = Dict().tag(sync=True)
    icon_label = Unicode().tag(sync=True)
    # Widgets
    icon: Instance[Icon] = InstanceDict(Icon, allow_none=True).tag(sync=True, **widget_serialization)


@register
class Panel(Box, HasApp):
    _model_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _model_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)
    _view_module = Unicode(_fe.module_name, read_only=True).tag(sync=True)
    _view_module_version = Unicode(_fe.module_version, read_only=True).tag(sync=True)

    _model_name = Unicode("PanelModel").tag(sync=True)
    _view_name = Unicode("PanelView").tag(sync=True)
    title: Instance[Title] = InstanceDict(Title, ()).tag(sync=True, **widget_serialization)
    class_name = Unicode("ipylab-panel").tag(sync=True)
    _comm = None

    def add_to_shell(
        self,
        *,
        area: Area = Area.main,
        activate: bool = True,
        mode: InsertMode = InsertMode.split_right,
        rank: int | None = None,
        ref: DisposableConnection | str = "",
        **options,
    ) -> Task[DisposableConnection]:
        """Add this panel to the shell."""
        return self.app.shell.add(self, area=area, mode=mode, activate=activate, rank=rank, ref=ref, **options)


@register
class SplitPanel(Panel):
    _model_name = Unicode("SplitPanelModel").tag(sync=True)
    _view_name = Unicode("SplitPanelView").tag(sync=True)
    orientation = Unicode("vertical").tag(sync=True)
    class_name = Unicode("ipylab-splitpanel").tag(sync=True)
    _force_update_in_progress = False

    # ============== Start temp fix =============
    # Below here is added as a temporary fix to address issue https://github.com/jtpio/ipylab/issues/129
    @observe("children")
    def _observe_children(self, _):
        self._rerender()

    def _rerender(self):
        """Toggle the orientation to cause lumino_widget.parent to re-render content."""

        async def _force_refresh(children):
            if children != self.children:
                return
            await asyncio.sleep(0.1)
            orientation = self.orientation
            self.orientation = "horizontal" if orientation == "vertical" else "vertical"
            await asyncio.sleep(0.001)
            self.orientation = orientation

        return self.app.to_task(_force_refresh(self.children))

    # ============== End temp fix =============

    def add_to_shell(
        self,
        *,
        area: Area = Area.main,
        activate: bool = True,
        mode: InsertMode = InsertMode.split_right,
        rank: int | None = None,
        ref: DisposableConnection | str = "",
        **options,
    ) -> Task[DisposableConnection]:
        task = super().add_to_shell(area=area, activate=activate, mode=mode, rank=rank, ref=ref, **options)

        async def _add_to_shell():
            result = await task
            await self._rerender()
            return result

        return self.app.to_task(_add_to_shell())
