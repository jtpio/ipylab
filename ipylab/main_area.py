# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio
import pathlib

from ipywidgets import register
from traitlets import Bool, Instance, Unicode, observe, validate

from ipylab.asyncwidget import AsyncWidgetBase, pack, widget_serialization
from ipylab.hasapp import HasApp
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Panel


@register
class MainArea(AsyncWidgetBase, HasApp):
    """A MainAreaWidget that can be loaded / unloaded with a single 'view'.

    Also provides methods to open/close a console using the context of the loaded widget.
    """

    _main_area_names: dict[str, MainArea] = {}
    _model_name = Unicode("MainAreaModel").tag(sync=True)

    path = Unicode(read_only=True).tag(sync=True)
    name = Unicode(read_only=True).tag(sync=True)
    loaded = Bool(read_only=True).tag(sync=True)
    console_loaded = Bool(read_only=True).tag(sync=True)
    content = Instance(Panel, (), read_only=True).tag(sync=True, **widget_serialization)

    @validate("name", "path")
    def _validate_name_path(self, proposal):
        trait = proposal["trait"].name
        if getattr(self, trait):
            raise RuntimeError(f"Changing the value of {trait=} is not allowed!")
        value = proposal["value"]
        if value != value.strip():
            raise ValueError(f"Leading/trailing whitespace is not allowed for {trait}: '{value}'")
        return value

    @observe("closed")
    def _observe_closed(self, change):
        if self.closed:
            self.loaded = False

    def __new__(cls, *, name: str, model_id=None, content: Panel = None, **kwgs):
        if not name:
            raise (ValueError("name not supplied"))
        if name in cls._main_area_names:
            return cls._main_area_names[name]
        inst = super().__new__(cls, name=name, **kwgs)
        return inst

    def __init__(self, *, name: str, path="", model_id=None, content: Panel = None, **kwgs):
        if self._model_id:
            return
        path_ = str(pathlib.PurePosixPath(path or name)).lower().strip("/")
        if path and path != path_:
            raise ValueError(
                f"`path` must be lowercase and not start/finish with '/' but got '{path}'"
            )
        self.set_trait("name", name)
        self.set_trait("path", path_)
        if content:
            self.set_trait("content", content)
        super().__init__(model_id=model_id, **kwgs)

    def close(self):
        self._main_area_names.pop(self.name, None)
        super().close()

    def load(
        self,
        *,
        content: Panel = None,
        area: Area = "main",
        activate: bool = True,
        mode: InsertMode = InsertMode.split_right,
        rank: int | None = None,
        ref: MainArea | None = None,
        class_name="ipylab-main-area",
    ) -> asyncio.Task:
        """Load into the shell.

        Use `unload` to remove it from the shell (will also close any open consoles).

        If it is in the shell, this will move it.
        content: [Panel]
            The content
        ref:
            The main area widget to use as a reference when inserting in the shell.
        name:
            The session name to use.
        class_name:
            The css class to add to the widget.
        """
        if content:
            self.set_trait("content", content)
        return self.schedule_operation(
            "load",
            area=area,
            options={"mode": mode, "rank": rank, "activate": activate, "ref": pack(ref)},
            className=class_name,
        )

    def unload(self) -> asyncio.Task:
        "Remove from the shell"
        return self.schedule_operation("unload")

    def load_console(
        self,
        *,
        name="Console",
        mode: InsertMode = InsertMode.split_bottom,
        **kwgs,
    ) -> asyncio.Task:
        """Load a console using for the same kernel.

        Opening the console will close any existing consoles.
        """
        return self.schedule_operation(
            "open_console", insertMode=InsertMode(mode), name=name, **kwgs
        )

    def unload_console(self) -> asyncio.Task:
        """Unload the console."""
        return self.schedule_operation("close_console")
