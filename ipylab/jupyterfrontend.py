#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget, widget_serialization
from traitlets import Instance, Unicode
from ._frontend import module_name, module_version

from .commands import CommandRegistry

class JupyterFrontEnd(Widget):
    """TODO: Make Singleton?
    """
    _model_name = Unicode('JupyterFrontEndModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    commands = Instance(CommandRegistry).tag(sync=True, **widget_serialization)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, commands=CommandRegistry(), **kwargs)
