#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio

from ipywidgets import CallbackDispatcher, Widget, register, widget_serialization
from traitlets import Instance, Unicode
from ._frontend import module_name, module_version

from .commands import CommandRegistry
from .menu import CustomMenu
from .toolbar import CustomToolbar
from .shell import Shell
from .sessions import SessionManager


@register
class JupyterFrontEnd(Widget):
    _model_name = Unicode("JupyterFrontEndModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    version = Unicode(read_only=True).tag(sync=True)
    shell = Instance(Shell).tag(sync=True, **widget_serialization)
    commands = Instance(CommandRegistry).tag(sync=True, **widget_serialization)
    sessions = Instance(SessionManager).tag(sync=True, **widget_serialization)
    menu = Instance(CustomMenu).tag(sync=True, **widget_serialization)
    toolbar = Instance(CustomToolbar).tag(sync=True, **widget_serialization)

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            shell=Shell(),
            commands=CommandRegistry(),
            sessions=SessionManager(),
            menu=CustomMenu(),
            toolbar=CustomToolbar(),
            **kwargs,
        )
        self._ready_event = asyncio.Event()
        self._on_ready_callbacks = CallbackDispatcher()
        self.on_msg(self._on_frontend_msg)
        self.menu.set_command_registry(self.commands)
        self.toolbar.set_command_registry(self.commands)

    def _on_frontend_msg(self, _, content, buffers):
        if content.get("event", "") == "lab_ready":
            self._ready_event.set()
            self._on_ready_callbacks()

    async def ready(self):
        await self._ready_event.wait()

    def on_ready(self, callback, remove=False):
        self._on_ready_callbacks.register_callback(callback, remove)
