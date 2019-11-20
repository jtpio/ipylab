# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget, widget_serialization
from traitlets import Unicode
from ._frontend import module_name, module_version


class Shell(Widget):
    _model_name = Unicode("ShellModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

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
            {"func": "expandLeft", "payload": {},}
        )

    def expand_right(self):
        self.send(
            {"func": "expandRight", "payload": {},}
        )
