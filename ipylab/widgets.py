# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import VBox
from traitlets import Unicode
from ._frontend import module_name, module_version


class Panel(VBox):
    _model_name = Unicode('PanelModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
