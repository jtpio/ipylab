# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine

from ipylab import TransformMode
from ipylab.hasapp import HasApp


class JupyterFrontEndSubsection(HasApp):
    """Use as a sub section in the JupyterFrontEnd class"""

    # Point to the attribute on the JupyterFrontEndModel for which this class represents.
    # Nested attributes are support such as "app.sessionManager"
    # see ipylab/src/widgets/frontend.ts -> JupyterFrontEndModel
    JFE_JS_SUB_PATH = ""

    def executeMethod(
        self,
        method: str,
        *args,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.raw,
    ) -> asyncio.Task:
        """Execute a nested method on this objects JFE_SUB_PATH relative to the instance of the
        JupyterFrontEndModel in the JS frontend.
        """
        # validation
        method = f"{self.JFE_JS_SUB_PATH}.{method}"
        return self.app.executeMethod(method, *args, callback=callback, transform=transform)

    def get_attribute(
        self,
        name: str,
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.raw,
    ) -> asyncio.Task:
        """A serialized version of the attribute relative to this object."""
        raise NotImplementedError("TODO")
        return self.app.get_attribute(
            f"{self.JFE_JS_SUB_PATH}.{name}",
            callback=callback,
            transform=transform,
        )

    def list_attributes(
        self,
        base: str = "",
        *,
        callback: Callable[[any, any], None | Coroutine] = None,
        transform: TransformMode | dict[str, str] = TransformMode.raw,
    ) -> asyncio.Task:
        """Get a list of all attributes"""
        raise NotImplementedError("TODO")
        return self.app.list_attributes(
            f"{self.JFE_JS_SUB_PATH}.{base}", callback=callback, transform=transform
        )
