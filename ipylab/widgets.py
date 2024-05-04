# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

from typing import TYPE_CHECKING

import ipywidgets as ipw
from ipywidgets import Box, DOMWidget, register, widget_serialization
from ipywidgets.widgets.trait_types import InstanceDict
from traitlets import Bool, Dict, Instance, Unicode

import ipylab._frontend as _fe
from ipylab.asyncwidget import WidgetBase
from ipylab.hasapp import HasApp
from ipylab.shell import Area, InsertMode

if TYPE_CHECKING:
    import asyncio


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
    closable = Bool(True).tag(sync=True)
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
    closed = Bool(read_only=True).tag(sync=True)

    def open(self) -> None:
        self._check_closed()
        super().open()

    def close(self) -> None:
        self.set_trait("closed", True)
        super().close()

    def _check_closed(self):
        if self.closed:
            msg = f"This object is closed {self}"
            raise RuntimeError(msg)

    def addToShell(
        self,
        *,
        area: Area = Area.main,
        mode: InsertMode = InsertMode.split_right,
        activate: bool = True,
        rank: int | None = None,
        ref: ipw.Widget | None = None,
        **options,
    ) -> asyncio.Task:
        """Add this panel to the shell.

        Parameters
        ----------

        area str
        ----
            The location

        args:
            ref mode: str
        """
        self._check_closed()
        return self.app.shell.addToShell(
            self, area=Area(area), mode=InsertMode(mode), activate=activate, rank=rank, ref=ref, **options
        )


@register
class SplitPanel(Panel):
    _model_name = Unicode("SplitPanelModel").tag(sync=True)
    _view_name = Unicode("SplitPanelView").tag(sync=True)
    orientation = Unicode("vertical").tag(sync=True)
    class_name = Unicode("ipylab-splitpanel").tag(sync=True)
