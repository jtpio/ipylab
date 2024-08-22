# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio
import contextlib
from typing import ClassVar

from ipywidgets import register
from traitlets import Unicode

from ipylab.asyncwidget import AsyncWidgetBase
from ipylab.jupyterfrontend_subsection import FrontEndSubsection


@register
class DisposableConnection(FrontEndSubsection, AsyncWidgetBase):
    """A connection to a disposable object in the Frontend.

    The dispose method is directly accesssable.

    Other attributes and methods are available using the corresponding built in methods.

    The comm trait can be observed for when the lumino widget in Jupyterlab is closed.

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    """

    SUB_PATH_BASE = "obj"
    _connections: ClassVar[dict[str, DisposableConnection]] = {}
    _model_name = Unicode("DisposableConnectionModel").tag(sync=True)
    id = Unicode(read_only=True).tag(sync=True)

    def __new__(cls, *, id: str, **kwgs):  # noqa: A002
        if id not in cls._connections:
            cls._connections[id] = super().__new__(cls, **kwgs)
        return cls._connections[id]

    def __init__(self, *, id: str, model_id=None, **kwgs):  # noqa: A002
        if self._async_widget_base_init_complete:
            return
        self.set_trait("id", id)
        super().__init__(model_id=model_id, **kwgs)

    def close(self):
        self._connections.pop(self.id, None)
        super().close()

    def dispose(self, *, just_coro=False):
        "Close the disposable on the frontend."

        async def dispose_():
            if self.comm:
                with contextlib.suppress(asyncio.CancelledError):
                    await self.execute_method("dispose", just_coro=True)

        return self.to_task(dispose_(), just_coro=just_coro)
