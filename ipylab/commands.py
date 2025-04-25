# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
import json
from collections import defaultdict

from ipywidgets import CallbackDispatcher, Widget, register
from traitlets import List, Unicode

from ._frontend import module_name, module_version


def _noop():
    pass


@register
class CommandPalette(Widget):
    _model_name = Unicode("CommandPaletteModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _items = List([], read_only=True).tag(sync=True)

    def add_item(self, command_id, category, *, args=None, rank=None):
        args = args or {}
        self.send(
            {
                "func": "addItem",
                "payload": {
                    "id": command_id,
                    "category": category,
                    "args": args,
                    "rank": rank,
                },
            }
        )


@register
class CommandRegistry(Widget):
    _model_name = Unicode("CommandRegistryModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _command_list = List(Unicode, read_only=True).tag(sync=True)
    _commands = List([], read_only=True).tag(sync=True)
    _execute_callbacks = defaultdict(_noop)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_msg(self._on_frontend_msg)

    def _on_frontend_msg(self, _, content, buffers):
        if content.get("event", "") == "execute":
            command_id = content.get("id")
            args = json.loads(content.get("args"))
            self._execute_callbacks[command_id](**args)

    def execute(self, command_id, args=None):
        args = args or {}
        self.send({"func": "execute", "payload": {"id": command_id, "args": args}})

    def list_commands(self):
        return self._command_list

    def add_command(
        self, command_id, execute, *, caption="", label="", icon_class="", icon=None
    ):
        if command_id in self._command_list:
            raise Exception(f"Command {command_id} is already registered")
        # TODO: support other parameters (isEnabled, isVisible...)
        self._execute_callbacks[command_id] = execute
        self.send(
            {
                "func": "addCommand",
                "payload": {
                    "id": command_id,
                    "caption": caption,
                    "label": label,
                    "iconClass": icon_class,
                    "icon": f"IPY_MODEL_{icon.model_id}" if icon else None,
                },
            }
        )

    def remove_command(self, command_id):
        # TODO: check whether to keep this method, or return disposables like in lab
        self.send({"func": "removeCommand", "payload": {"id": command_id}})
