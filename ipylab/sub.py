# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
from typing import Callable, Coroutine

import ipylab


class HasApp:
    @property
    def app(self) -> ipylab.JupyterFrontEnd:
        if not hasattr(self, "_app"):
            self._app = ipylab.JupyterFrontEnd()
        return self._app


class SubApp(HasApp):
    """for providing nested access to subpaths inside an app."""

    SUBPATH = ""

    def execute_method(
        self,
        method: str,
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        **kwgs,
    ) -> asyncio.Task:
        "Calls app.execute_method with method={self.SUBPATH}.{method}."
        return self.app.execute_method(f"{self.SUBPATH}.{method}", callback=callback, **kwgs)
