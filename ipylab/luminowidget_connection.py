# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

from typing import ClassVar

from ipywidgets import register
from traitlets import Unicode

from ipylab.asyncwidget import AsyncWidgetBase
from ipylab.hasapp import HasApp


@register
class LuminoWidgetConnection(AsyncWidgetBase, HasApp):
    """A connection to a single Lumino widget in the Jupyterlab shell.

    The comm trait can be observed for when the lumino widget in Jupyterlab is closed.

    There is no direct connection to the widget on the frontend, rather, it
    can be accessed using the prefix 'widget.' in the method calls:
    * execute_method
    """

    _connections: ClassVar[dict[str, LuminoWidgetConnection]] = {}
    _model_name = Unicode("LuminoWidgetConnectionModel").tag(sync=True)
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

    def dispose(self):
        """Close the Lumino widget at the frontend.

        Note: The task is cancelled when the connection is closed."""
        return self.execute_method("widget.dispose")
