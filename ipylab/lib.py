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
def on_frontend_error(obj: AsyncWidgetBase, error: str, msg: dict) -> t.NoReturn:
    from ipylab.asyncwidget import IpylabFrontendError

    raise IpylabFrontendError(
        f"{obj.__class__.__name__} operation '{msg.get('operation')}' failed with message '{error}'"
    )
