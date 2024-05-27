# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING, ClassVar

from ipywidgets import register
from traitlets import Instance, TraitType, Unicode, UseEnum, observe, validate

from ipylab.asyncwidget import AsyncWidgetBase, widget_serialization
from ipylab.hasapp import HasApp
from ipylab.shell import Area, InsertMode
from ipylab.widgets import Panel

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

if TYPE_CHECKING:
    import asyncio


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

    _main_area_names: ClassVar[dict[str, MainArea]] = {}
    _model_name = Unicode("MainAreaModel").tag(sync=True)

    path = Unicode(read_only=True).tag(sync=True)
    name = Unicode(read_only=True).tag(sync=True)
    content = Instance(Panel, (), read_only=True).tag(sync=True, **widget_serialization)
    status: TraitType[ViewStatus, ViewStatus] = UseEnum(ViewStatus, read_only=True).tag(sync=True)
    console_status: TraitType[ViewStatus, ViewStatus] = UseEnum(ViewStatus, read_only=True).tag(sync=True)

    @validate("name", "path")
    def _validate_name_path(self, proposal):
        trait = proposal["trait"].name
        if getattr(self, trait):
            msg = f"Changing the value of {trait=} is not allowed!"
            raise RuntimeError(msg)
        value = proposal["value"]
        if value != value.strip():
            msg = f"Leading/trailing whitespace is not allowed for {trait}: '{value}'"
            raise ValueError(msg)
        return value

    @observe("comm")
    def _observe_comm(self, _):
        if not self.comm:
            self.set_trait("status", ViewStatus.unloaded)
            self.set_trait("console_status", ViewStatus.unloaded)

    def __new__(cls, *, name: str, model_id=None, content: Panel | None = None, **kwgs):  # noqa: ARG003
        if not name:
            msg = "name not supplied"
            raise (ValueError(msg))
        if name in cls._main_area_names:
            return cls._main_area_names[name]
        return super().__new__(cls, name=name, **kwgs)

    def __init__(self, *, name: str, path="", model_id=None, content: Panel | None = None, **kwgs):
        if self._model_id:
            return
        path_ = str(pathlib.PurePosixPath(path or name)).lower().strip("/")
        if path and path != path_:
            msg = f"`path` must be lowercase and not start/finish with '/' but got '{path}'"
            raise ValueError(msg)
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
        content: Panel | None = None,
        area: Area = Area.main,
        activate: bool = True,
        mode: InsertMode = InsertMode.tab_after,
        rank: int | None = None,
        ref: str = "",
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
            The id of the widget to insert relative to in the shell. (default is app.current_widget_id).
        name:
            The session name to use.
        class_name:
            The css class to add to the widget.
        """
        if content:
            self.set_trait("content", content)
        self.set_trait("status", ViewStatus.loading)
        options = {
            "mode": InsertMode(mode),
            "rank": rank,
            "activate": activate,
            "ref": ref or self.app.current_widget_id,
        }
        return self.schedule_operation("load", area=area, options=options, className=class_name)

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
        return self.schedule_operation("open_console", insertMode=InsertMode(mode), name=name, **kwgs)

    def unload_console(self) -> asyncio.Task:
        """Unload the console."""
        self.set_trait("console_status", ViewStatus.unloading)
        return self.schedule_operation("close_console")
