# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import VBox, Widget, register, widget_serialization
from traitlets import Bool, Dict, Instance, Unicode
from ._frontend import module_name, module_version
from .icon import Icon


@register
class Title(Widget):
    _model_name = Unicode("TitleModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    label = Unicode().tag(sync=True)
    icon_class = Unicode().tag(sync=True)
    caption = Unicode().tag(sync=True)
    class_name = Unicode().tag(sync=True)
    closable = Bool(True).tag(sync=True)
    dataset = Dict().tag(sync=True)
    icon_label = Unicode().tag(sync=True)

    icon = Instance(Icon, allow_none=True).tag(sync=True, **widget_serialization)


@register
class Panel(VBox):
    _model_name = Unicode("PanelModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    title = Instance(Title).tag(sync=True, **widget_serialization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, title=Title(), **kwargs)


@register
class SplitPanel(Panel):
    _model_name = Unicode("SplitPanelModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode("SplitPanelView").tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    orientation = Unicode("vertical").tag(sync=True)

    def addWidget(self, widget):
        self.children = list(self.children) + [widget]
