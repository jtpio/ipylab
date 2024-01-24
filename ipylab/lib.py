# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import typing as t

import ipylab

if t.TYPE_CHECKING:
    from ipylab.asyncwidget import AsyncWidgetBase


@ipylab.hookimpl
def get_ipylab_backend_class():
    import ipylab.labapp

    return ipylab.labapp.IPLabApp


@ipylab.hookimpl
def unhandled_frontend_operation_message(obj: AsyncWidgetBase, operation: str):
    raise RuntimeError(f"Unhandled frontend_operation_message from {obj=} {operation=}")
