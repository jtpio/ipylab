# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING

from ipylab import TransformMode
from ipylab.asyncwidget import AsyncWidgetBase

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Literal

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
    ):
        """Execute a nested method on this objects JFE_SUB_PATH relative to the instance of the
        JupyterFrontEndModel in the JS frontend.
        """
        return super().execute_method(
            method if method in ["getAttribute", "setAttribute"] else f"{self.SUB_PATH_BASE}.{method}",
            *args,
            transform=transform,
            toLuminoWidget=toLuminoWidget,
        )

    def get_attribute(
        self,
        path: str,
        *,
        transform: TransformType = TransformMode.raw,
        ifMissing: Literal["raise", "null"] = "raise",
    ):
        """Get an attribute by name from the front end."""
        return super().get_attribute(f"{self.SUB_PATH_BASE}.{path}", transform=transform, ifMissing=ifMissing)

    def set_attribute(
        self,
        path: str,
        value,
        valueTransform: TransformType = TransformMode.raw,
        *,
        valueToLuminoWidget=False,
    ):
        """Set an attribute on the object in the frontend based on the object to which this refers."""
        return super().set_attribute(
            f"{self.SUB_PATH_BASE}.{path}",
            value,
            valueTransform,
            valueToLuminoWidget=valueToLuminoWidget,
        )

    def list_attributes(self, path: str = "", *, transform: TransformType = TransformMode.raw):
        """Get a list of all attributes."""
        return super().list_attributes(f"{self.SUB_PATH_BASE}.{path}", transform=transform)
