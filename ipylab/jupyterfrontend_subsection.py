# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING

from ipylab import TransformMode
from ipylab.hasapp import HasApp

if TYPE_CHECKING:
    import asyncio

    from ipylab.asyncwidget import CallbackType, TransformType


class JupyterFrontEndSubsection(HasApp):
    """Use as a sub section in the JupyterFrontEnd class"""

    # Point to the attribute on the JupyterFrontEndModel for which this class represents.
    # Nested attributes are support such as "app.sessionManager"
    # see ipylab/src/widgets/frontend.ts -> JupyterFrontEndModel
    JFE_JS_SUB_PATH = ""

    def executeMethod(
        self, method: str, *args, callback: CallbackType | None = None, transform: TransformType = TransformMode.raw
    ) -> asyncio.Task:
        """Execute a nested method on this objects JFE_SUB_PATH relative to the instance of the
        JupyterFrontEndModel in the JS frontend.
        """
        # validation
        method = f"{self.JFE_JS_SUB_PATH}.{method}"
        return self.app.executeMethod(method, *args, callback=callback, transform=transform)

    def get_attribute(
        self, name: str, *, callback: CallbackType | None = None, transform: TransformType = TransformMode.raw
    ) -> asyncio.Task:
        """A serialized version of the attribute relative to this object."""
        msg = "TODO"
        raise NotImplementedError(msg)
        return self.app.get_attribute(
            f"{self.JFE_JS_SUB_PATH}.{name}",
            callback=callback,
            transform=transform,
        )

    def list_attributes(
        self,
        base: str = "",
        *,
        callback: CallbackType | None = None,
        transform: TransformType = TransformMode.raw,
    ) -> asyncio.Task:
        """Get a list of all attributes"""
        msg = "TODO"
        raise NotImplementedError(msg)
        return self.app.list_attributes(f"{self.JFE_JS_SUB_PATH}.{base}", callback=callback, transform=transform)
