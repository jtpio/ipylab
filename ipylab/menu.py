# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from ipywidgets import Widget, register
from traitlets import List, Unicode
from ._frontend import module_name, module_version
from .commands import CommandRegistry


@register
class CustomMenu(Widget):
    _model_name = Unicode("CustomMenuModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _menu_list = List(Unicode, read_only=True).tag(sync=True)
    commands = None

    def set_command_registry(self, commands: CommandRegistry):
        if self.commands is not None:
            raise ValueError("Cannot set command registry twice")
        self.commands = commands

    def insert_snippet(self, snippet):
        self.commands.execute("custom-menu:snippet", snippet)

    def run_snippet(self, snippet):
        self.commands.execute("custom-menu:run-snippet", snippet)

    def add_menu(self, title, spec, className=None) -> None:
        if title in self._menu_list:
            raise Exception(f"Menu {title} is already registered")

        if self.commands is None:
            raise Exception("No command registry")

        self.send(
            {
                "func": "addMenu",
                "payload": {
                    "title": title,
                    "spec": self._compile_spec(title, spec),
                    "className": className,
                },
            }
        )

    def remove_menu(self, title) -> None:
        if self.commands is None:
            raise Exception("No command registry")

        if title in self._menu_list:
            self.send(
                {
                    "func": "removeMenu",
                    "payload": {
                        "title": title,
                    },
                }
            )

    def is_separator(self, s):
        return s == "separator" or all(c == "-" for c in s)

    def _compile_spec(self, title, spec):
        result = []
        for entry in spec:
            if isinstance(entry, str):
                if self.is_separator(entry):
                    result.append({"type": "separator"})
                else:
                    raise Exception(f"unknown menu entry '{entry}'")
            elif "name" not in entry:
                raise Exception("invalid menu entry '{entry}'; 'name' is missing.")
            else:
                name = entry["name"]
                if "sub-menu" in entry:
                    type = "submenu"
                    payload = self._compile_spec(f"{title}:{name}", entry["sub-menu"])
                elif "command" in entry:

                    def cmd(cmd):
                        return lambda: self.commands.execute(cmd)

                    type = "command"
                    payload = f"custom-menu:run-command:{title}:{name}"
                    try:
                        execute = (
                            cmd(entry["command"])
                            if isinstance(entry["command"], str)
                            else entry["command"]
                        )
                        self.commands.add_command(
                            payload, execute=execute, label=entry["name"]
                        )
                    except:
                        pass
                else:
                    raise Exception(f"unknown menu entry '{entry}'")
                result.append({"name": name, "payload": payload, "type": type})
        return result
