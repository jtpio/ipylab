# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
from typing import Callable, Coroutine

import ipylab
from ipylab import TransformMode


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
        *args,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.done,
    ) -> asyncio.Task:
        "Calls app.execute_method with method={self.SUBPATH}.{method}."
        # validation
        return self.app.execute_method(
            f"{self.SUBPATH}.{method}", *args, callback=callback, transform=transform
        )

    def get_attribute(
        self,
        name: str,
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.done,
    ) -> asyncio.Task:
        """A serialized verison of the attribute relative to this object."""
        raise NotImplementedError("TODO")
        return self.app.get_attribute(
            f"{self.SUBPATH}.{name}",
            callback=callback,
            transform=transform,
        )

    def list_attributes(
        self,
        base: str = "",
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.done,
    ) -> asyncio.Task:
        """Get a list of all attributes"""
        raise NotImplementedError("TODO")
        return self.app.list_attributes(
            f"{self.SUBPATH}.{base}", callback=callback, transform=transform
        )
