# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import traitlets
from ipywidgets import TypedTuple
from traitlets import Container, Instance, Unicode

from ipylab._compat.typing import NotRequired, TypedDict
from ipylab.asyncwidget import AsyncWidgetBase, Transform, pack, register
from ipylab.common import NotificationType
from ipylab.connection import Connection

if TYPE_CHECKING:
    from asyncio import Task
    from collections.abc import Callable, Iterable
    from typing import Any


__all__ = ["NotificationManager"]


class NotifyAction(TypedDict):
    label: str
    callback: Callable[[], Any]
    display_type: NotRequired[Literal["default", "accent", "warn", "link"]]
    keep_open: NotRequired[bool]
    caption: NotRequired[str]


class ActionConnection(Connection):
    callback = traitlets.Callable()


class NotificationConnection(Connection):
    actions: Container[tuple[ActionConnection, ...]] = TypedTuple(trait=Instance(ActionConnection))

    def update(
        self,
        message: str,
        type: NotificationType | None = None,  # noqa: A002
        *,
        auto_close: float | Literal[False] | None = None,
        actions: Iterable[NotifyAction | ActionConnection] = (),
    ) -> Task[bool]:
        args = {
            "id": self.id,
            "message": message,
            "type": NotificationType(type) if type else None,
            "autoClose": auto_close,
        }

        async def update():
            actions_ = [await self.app.notification._ensure_action(v) for v in actions]  # noqa: SLF001
            if actions_:
                args["actions"] = list(map(pack, actions_))  # type: ignore
                to_object = [f"options.actions.{i}" for i in range(len(actions_))]
            else:
                to_object = None
            result = await self.app.notification.execute_method("update", args, toObject=to_object)
            for action in actions_:
                await self._add_to_tuple_trait("actions", action)
            return result

        return self.to_task(update())


@register
class NotificationManager(AsyncWidgetBase):
    """Create new notifications with access to the notification manager.

    ref: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#notifications
    """

    _model_name = Unicode("NotificationManagerModel").tag(sync=True)
    _basename = Unicode("notificationManager").tag(sync=True)
    SINGLETON = True
    notifications: Container[tuple[NotificationConnection, ...]] = TypedTuple(trait=Instance(NotificationConnection))

    async def _do_operation_for_frontend(self, operation: str, payload: dict, buffers: list):
        """Overload this function as required."""
        match operation:
            case "action callback":
                return ActionConnection.get_existing_connection(payload["cid"]).callback()
        return await super()._do_operation_for_frontend(operation, payload, buffers)

    async def _ensure_action(self, value: ActionConnection | NotifyAction) -> ActionConnection:
        "Create a new action."
        if not isinstance(value, dict):
            action = ActionConnection.get_existing_connection(str(value))
            value = action.info | {"callback": action.callback}  # type: ignore
        return await self.new_action(**value)  # type: ignore

    def notify(
        self,
        message: str,
        type: NotificationType = NotificationType.default,  # noqa: A002
        *,
        auto_close: float | Literal[False] | None = None,
        actions: Iterable[NotifyAction | ActionConnection] = (),
    ) -> Task[NotificationConnection]:
        """Create a new notification.

        To update a notification use the update method of the returned `NotificationConnection`.

        NotifyAction:
            label: str
            callback: Callable[[], Any]
            display_type: NotRequired[Literal["default", "accent", "warn", "link"]]
            keep_open: NotRequired[bool]
            caption: NotRequired[str]
        """

        options = {
            "message": message,
            "type": NotificationType(type) if type else None,
            "autoClose": auto_close,
        }

        async def notify():
            actions_ = [await self._ensure_action(v) for v in actions]
            if actions_:
                options["actions"] = list(map(pack, actions_))  # type: ignore
            notification: NotificationConnection = await self.schedule_operation(
                "notification",
                type=NotificationType(type),
                message=message,
                options=options,
                transform={
                    "transform": Transform.connection,
                    "cid": NotificationConnection.new_cid(),
                    "auto_dispose": True,
                },
                toObject=[f"options.actions.{i}" for i in range(len(actions_))] if actions_ else None,
            )
            for action in actions_:
                await notification._add_to_tuple_trait("actions", action)  # noqa: SLF001
            await self._add_to_tuple_trait("notifications", notification)
            return notification

        return self.to_task(notify())

    def new_action(
        self,
        label: str,
        callback: Callable[[], Any],
        display_type: Literal["default", "accent", "warn", "link"] = "default",
        *,
        keep_open: bool = False,
        caption: str = "",
    ) -> Task[ActionConnection]:
        "Create an action to use in a notification."
        cid = ActionConnection.new_cid()
        info = {"label": label, "displayType": display_type, "keep_open": keep_open, "caption": caption}
        task = self.schedule_operation(
            "createAction",
            **info,
            cid=cid,
            transform={"transform": Transform.connection, "cid": cid, "auto_dispose": True, "info": info},
        )

        async def new_action():
            action: ActionConnection = await task
            action.set_trait("callback", callback)
            return action

        return self.to_task(new_action())
