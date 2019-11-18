# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget
from traitlets import List, Unicode
from ._frontend import module_name, module_version


class CommandRegistry(Widget):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _commands = List(Unicode, read_only=True).tag(sync=True)

    def execute(self, command, args=None):
        args = args or {}
        self.send({"func": "execute", "payload": {"command": command, "args": args}})

    def list_commands(self):
        return self._commands
