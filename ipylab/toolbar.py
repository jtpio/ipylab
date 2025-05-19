# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget, register
from traitlets import List, Unicode
from ._frontend import module_name, module_version
from .icon import Icon
from .commands import CommandRegistry


@register
class CustomToolbar(Widget):
    _model_name = Unicode("CustomToolbarModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _toolbar_buttons = List(Unicode, read_only=True).tag(sync=True)
    commands = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_msg(self._on_frontend_msg)

    def set_command_registry(self, commands: CommandRegistry):
        if self.commands is not None:
            raise ValueError("Cannot set command registry twice")
        self.commands = commands

    def _on_frontend_msg(self, _, content, buffers):
        pass

    def add_button(
        self,
        name,
        execute,
        args=None,
        iconClass=None,
        icon=None,
        label=None,
        after=None,
        tooltip=None,
        className=None,
    ) -> None:
        if name in self._toolbar_buttons:
            raise Exception(f"Button {name} is already registered")
        iconMsg = None
        if isinstance(icon, Icon):
            iconMsg = f"IPY_MODEL_{icon.model_id}"
        elif isinstance(icon, str):
            iconMsg = icon

        if callable(execute):
            commandname = f"button_{name}_{execute.__name__}"
            self.commands.add_command(commandname, execute=execute, label=name)
            execute = commandname
        elif not isinstance(execute, str):
            raise TypeError("execute must be a str or callable")

        self.send(
            {
                "func": "addToolbarButton",
                "payload": {
                    "name": name,
                    "execute": execute,
                    "args": args or {},
                    "icon": iconMsg,
                    "iconClass": iconClass,
                    "label": label,
                    "tooltip": tooltip,
                    "after": after,
                    "className": className,
                },
            }
        )

    def remove_button(self, name) -> None:
        if name not in self._toolbar_buttons:
            raise Exception(f"unknown button {name}")
        self.send(
            {
                "func": "removeToolbarButton",
                "payload": {
                    "name": name,
                },
            }
        )

    def list_toolbar_buttons(self):
        return self._toolbar_buttons
