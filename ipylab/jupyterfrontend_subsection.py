# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING

from ipylab import TransformMode
from ipylab.hasapp import HasApp

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Iterable

    from ipylab.asyncwidget import CallbackType, TransformType


class JupyterFrontEndSubsection(HasApp):
    """Use as a sub section in the JupyterFrontEnd class"""

    # Point to the attribute on the JupyterFrontEndModel for which this class represents.
    # Nested attributes are support such as "app.sessionManager"
    # see ipylab/src/widgets/frontend.ts -> JupyterFrontEndModel
    JFE_JS_SUB_PATH = ""

    def execute_method(
        self,
        method: str,
        *args,
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
    ) -> asyncio.Task:
        """Execute a nested method on this objects JFE_SUB_PATH relative to the instance of the
        JupyterFrontEndModel in the JS frontend.
        """
        return self.app.execute_method(
            f"{self.JFE_JS_SUB_PATH}.{method}",
            *args,
            callback=callback,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
        )

    def get_attribute(
        self, path: str, *, callback: CallbackType | None = None, transform: TransformType = TransformMode.raw
    ) -> asyncio.Task:
        """Get an attribute by name from the front end."""
        return self.app.get_attribute(f"{self.JFE_JS_SUB_PATH}.{path}", callback=callback, transform=transform)

    def list_attributes(
        self,
        path: str = "",
        *,
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
    ) -> asyncio.Task:
        """Get a list of all attributes."""
        return self.app.list_attributes(f"{self.JFE_JS_SUB_PATH}.{path}", callback=callback, transform=transform)
