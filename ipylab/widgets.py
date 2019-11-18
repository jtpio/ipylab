# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import VBox
from traitlets import Unicode
from ._frontend import module_name, module_version


class Panel(VBox):
    _model_name = Unicode("PanelModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)


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
