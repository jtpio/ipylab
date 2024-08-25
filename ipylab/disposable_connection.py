# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import asyncio
import contextlib
from typing import Generic, TypeVar

from ipywidgets import register
from traitlets import Unicode

from ipylab.asyncwidget import AsyncWidgetBase
from ipylab.jupyterfrontend_subsection import FrontEndSubsection

T = TypeVar("T", bound="DisposableConnection")


@register
class DisposableConnection(FrontEndSubsection, AsyncWidgetBase, Generic[T]):
    """A connection to a disposable object in the Frontend.

    The dispose method is directly accesssable.

    Other attributes and methods are available using the corresponding built in methods.

    The comm trait can be observed for when the lumino widget in Jupyterlab is closed.

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    Subclasses that are inherited with and ID_PREFIX
    """

    SUB_PATH_BASE = "obj"
    ID_PREFIX = ""
    _CLASS_DEFINITIONS: dict[str, type[T]] = {}  # noqa RUF012
    _connections: dict[str, T] = {}  # noqa RUF012
    _model_name = Unicode("DisposableConnectionModel").tag(sync=True)
    id = Unicode(read_only=True).tag(sync=True)

    def __init_subclass__(cls, **kwargs) -> None:
        if cls.ID_PREFIX:
            cls._CLASS_DEFINITIONS[cls.ID_PREFIX] = cls  # type: ignore
        super().__init_subclass__(**kwargs)

    def __new__(cls, *, id: str, **kwgs):  # noqa A002
        if id not in cls._connections:
            if cls.ID_PREFIX and not id.startswith(cls.ID_PREFIX):
                msg = f"Expected prefix '{cls.ID_PREFIX}' not found for {id=}"
                raise ValueError(msg)
            # Check if a subclass is registered with 'ID_PREFIX'
            cls_ = cls._CLASS_DEFINITIONS.get(id.split(":")[0], cls) if ":" in id else cls
            cls._connections[id] = super().__new__(cls_, **kwgs)  # type: ignore
        return cls._connections[id]

    def __str__(self):
        return self.id

    @classmethod
    def to_id(cls, name_or_id: str | T) -> str:
        """Generate an id for the given name."""
        if isinstance(name_or_id, DisposableConnection):
            return name_or_id.id
        if not cls.ID_PREFIX:
            return name_or_id
        return f"{cls.ID_PREFIX}:{name_or_id.removeprefix(cls.ID_PREFIX).strip(':')}"

    def __init__(self, *, id: str, model_id=None, **kwgs):  # noqa: A002
        if self._async_widget_base_init_complete:
            return
        self.set_trait("id", id)
        super().__init__(model_id=model_id, **kwgs)

    def close(self):
        self._connections.pop(self.id, None)
        super().close()

    def dispose(self):
        "Close the disposable on the frontend."

        async def dispose_():
            if self.comm:
                with contextlib.suppress(asyncio.CancelledError):
                    await self.execute_method("dispose")

        return self.to_task(dispose_())

    @classmethod
    def get_existing_connection(cls, name_or_id: str | T):
        "Get an existing connection"
        return cls._connections.get(cls.to_id(name_or_id))
