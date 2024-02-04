# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio
import pathlib
import sys

from ipywidgets import register
from traitlets import Instance, Unicode, UseEnum, observe, validate

from ipylab.asyncwidget import AsyncWidgetBase, pack, widget_serialization
from ipylab.hasapp import HasApp
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Panel

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


class ViewStatus(StrEnum):
    unloaded = "unloaded"
    loaded = "loaded"
    loading = "loading"
    unloading = "unloading"


@register
class MainArea(AsyncWidgetBase, HasApp):
    """A MainAreaWidget that can be loaded / unloaded with a single 'view'.

    Also provides methods to open/close a console using the context of the loaded widget.
    """

    _main_area_names: dict[str, MainArea] = {}
    _model_name = Unicode("MainAreaModel").tag(sync=True)

    path = Unicode(read_only=True).tag(sync=True)
    name = Unicode(read_only=True).tag(sync=True)
    content = Instance(Panel, (), read_only=True).tag(sync=True, **widget_serialization)
    status = UseEnum(ViewStatus, read_only=True).tag(sync=True)
    console_status = UseEnum(ViewStatus, read_only=True).tag(sync=True)

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
            self.set_trait("status", ViewStatus.unloaded)
            self.set_trait("console_status", ViewStatus.unloaded)

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

        Only one main_area_widget (view) can exist at a time, any existing widget will be disposed
        prior to loading a new widget.

        When this function is call the trait `status` will be set to 'loading'. It will change to 'loaded' once
        the widget has been loaded in the Frontend.

        Use `unload` to dispose the widget from the shell (will also close the linked console if it is open).

        content: [Panel]
            The content
        ref:
            The main area widget to use as a reference when inserting in the shell.
        name:
            The session name to use.
        class_name:
            The css class to add to the widget.
        """
        self._check_closed()
        if content:
            self.set_trait("content", content)
        self.set_trait("status", ViewStatus.loading)
        return self.schedule_operation(
            "load",
            area=area,
            options={"mode": mode, "rank": rank, "activate": activate, "ref": pack(ref)},
            className=class_name,
        )

    def unload(self) -> asyncio.Task:
        "Remove from the shell"
        self.set_trait("status", ViewStatus.unloading)
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
        self.set_trait("console_status", ViewStatus.loading)
        return self.schedule_operation(
            "open_console", insertMode=InsertMode(mode), name=name, **kwgs
        )

    def unload_console(self) -> asyncio.Task:
        """Unload the console."""
        self.set_trait("console_status", ViewStatus.unloading)
        return self.schedule_operation("close_console")
