# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget, register, widget_serialization
from traitlets import List, Unicode
from ._frontend import module_name, module_version


@register
class Shell(Widget):
    _model_name = Unicode("ShellModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _widgets = List([], read_only=True).tag(sync=True)

    def add(self, widget, area, args=None):
        args = args or {}
        serialized_widget = widget_serialization["to_json"](widget, None)
        self.send(
            {
                "func": "add",
                "payload": {
                    "serializedWidget": serialized_widget,
                    "area": area,
                    "args": args,
                },
            }
        )

    def expand_left(self):
        self.send(
            {
                "func": "expandLeft",
                "payload": {},
            }
        )

    def expand_right(self):
        self.send(
            {
                "func": "expandRight",
                "payload": {},
            }
        )
