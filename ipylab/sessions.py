#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import asyncio

from ipywidgets import CallbackDispatcher, Widget, register, widget_serialization
from traitlets import List, Unicode, Dict

from ._frontend import module_name, module_version


@register
class SessionManager(Widget):
    """Expose JupyterFrontEnd.serviceManager.sessions"""

    _model_name = Unicode("SessionManagerModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    # information of the current session
    current_session = Dict(read_only=True).tag(sync=True)
    # keeps track of the list of sessions
    sessions = List([], read_only=True).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._refreshed_event = None
        self._on_refresh_callbacks = CallbackDispatcher()
        self.on_msg(self._on_frontend_msg)

    def _on_frontend_msg(self, _, content, buffers):
        if content.get("event", "") == "sessions_refreshed":
            self._refreshed_event.set()
            self._on_refresh_callbacks()

    async def refresh_running(self):
        """Force a call to refresh running sessions

        Resolved when `SessionManager.runnigSession` resolves
        """
        self.send({"func": "refreshRunning"})
        self._refreshed_event = asyncio.Event()
        await self._refreshed_event.wait()

    def running(self):
        """List all running sessions managed in the manager"""
        return self.sessions
