# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import DOMWidget, register
from traitlets import Unicode, Float
from ._frontend import module_name, module_version


@register
class Icon(DOMWidget):
    _model_name = Unicode("IconModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode("IconView").tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    name = Unicode().tag(sync=True)
    svgstr = Unicode().tag(sync=True)
