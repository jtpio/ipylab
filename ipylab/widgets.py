# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio

import ipywidgets as ipw
from ipywidgets import Box, Layout, Widget, register, widget_serialization
from ipywidgets.widgets.trait_types import InstanceDict
from traitlets import Bool, Dict, Unicode

import ipylab.jupyterfrontend as _jfe
from ipylab.asyncwidget import WidgetBase
from ipylab.shell import Area, InsertMode


@register
class Icon(WidgetBase):
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
    icon = InstanceDict(Icon, allow_none=True).tag(sync=True, **widget_serialization)


@register
class Panel(Box, WidgetBase):
    _model_name = Unicode("PanelModel").tag(sync=True)
    _view_name = Unicode("PanelView").tag(sync=True)
    title = InstanceDict(Title, ()).tag(sync=True, **widget_serialization)
    class_name = Unicode("ipylab-panel").tag(sync=True)

    @property
    def app(self):
        return _jfe.JupyterFrontEnd()

    def add_to_shell(
        self,
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
        return self.app.shell.add(
            self,
            Area(area),
            mode=InsertMode(mode),
            activate=activate,
            rank=rank,
            ref=ref,
            **options,
        )


@register
class SplitPanel(Panel):
    _model_name = Unicode("SplitPanelModel").tag(sync=True)
    _view_name = Unicode("SplitPanelView").tag(sync=True)
    orientation = Unicode("vertical").tag(sync=True)
    class_name = Unicode("ipylab-splitpanel").tag(sync=True)
    layout = InstanceDict(Layout, kw={"min_height": "100px"}).tag(sync=True, **widget_serialization)


del Widget, Layout
