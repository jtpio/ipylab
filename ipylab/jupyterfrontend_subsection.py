# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING

from ipylab import TransformMode
from ipylab.asyncwidget import AsyncWidgetBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ipylab.asyncwidget import TransformType


class FrontEndSubsection(AsyncWidgetBase):
    """Direct access to methods on an object relative to the frontend Model."""

    # Point to the attribute on the model to which this model corresponds.
    # Nested attributes are support such as "app.sessionManager"
    # see ipylab/src/widgets/ipylab.ts -> IpylabModel
    SUB_PATH_BASE = "app"

    def execute_method(
        self,
        method: str,
        *args,
        transform: TransformType = TransformMode.raw,
        toLuminoWidget: Iterable[str] | None = None,
        just_coro=False,
    ):
        """Execute a nested method on this objects JFE_SUB_PATH relative to the instance of the
        JupyterFrontEndModel in the JS frontend.
        """

        return super().execute_method(
            f"{self.SUB_PATH_BASE}.{method}",
            *args,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
            just_coro=just_coro,
        )

    def get_attribute(self, path: str, *, transform: TransformType = TransformMode.raw, just_coro=False):
        """Get an attribute by name from the front end."""
        return super().get_attribute(f"{self.SUB_PATH_BASE}.{path}", transform=transform, just_coro=just_coro)

    def list_attributes(self, path: str = "", *, transform: TransformType = TransformMode.raw, just_coro=False):
        """Get a list of all attributes."""
        return super().list_attributes(f"{self.SUB_PATH_BASE}.{path}", transform=transform, just_coro=just_coro)
