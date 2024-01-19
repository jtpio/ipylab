# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio
import typing as t


from ipylab.asyncwidget import Widget, pack

if t.TYPE_CHECKING:
    from ipylab.jupyterfrontend import JupyterFrontEnd


class Dialog:
    def __init__(self, app: JupyterFrontEnd) -> None:
        self._app = app

    @property
    def app(self):
        return self._app

    def get_boolean(self, title: str) -> asyncio.Task:
        """Jupyter dialog to get a boolean value.
        see: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#input-dialogs
        """
        return self.app.schedule_operation("getBoolean", title=title)

    def get_item(self, title: str, items: tuple | list) -> asyncio.Task:
        """Jupyter dialog to get an item from a list value.

        note: will always return a string representation of the selected item.
        see: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#input-dialogs
        """
        return self.app.schedule_operation("getItem", title=title, items=tuple(items))

    def get_number(self, title: str) -> asyncio.Task:
        """Jupyter dialog to get a number.
        see: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#input-dialogs
        """
        return self.app.schedule_operation("getNumber", title=title)

    def get_text(self, title: str) -> asyncio.Task:
        """Jupyter dialog to get a string.
        see: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#input-dialogs
        """
        return self.app.schedule_operation("getText", title=title)

    def get_password(self, title: str) -> asyncio.Task:
        """Jupyter dialog to get a number.
        see: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#input-dialogs
        """
        return self.app.schedule_operation("getPassword", title=title)

    def show_dialog(
        self, title: str = "", body: str | Widget = "", host: None | Widget = None, **kwgs
    ):
        """Jupyter dialog to get user response with custom buttons and checkbox.

            returns {'value':any, 'isChecked':bool|None}

            'value' is the button 'accept' value of the selected button.

            title: 'Dialog title', // Can be text or a react element
            body: 'Dialog body', // Can be text, a widget or a react element
            host: document.body, // Parent element for rendering the dialog
            specify kwgs passed as below.
            buttons: [ // List of buttons
            buttons=[
            {
                "ariaLabel": "Accept",
                "label": "Accept",
                "iconClass": "",
                "iconLabel": "",
                "caption": "Accept the result",
                "className": "",
                "accept": False,
                "actions": [],
                "displayType": "warn",
            },
            {
                "ariaLabel": "Cancel",
                "label": "Cancel",
                "iconClass": "",
                "iconLabel": "",
                "caption": "",
                "className": "",
                "accept": False,
                "actions": [],
                "displayType": "default",
            },
        ],
        ],
            ],
            checkbox: { // Optional checkbox in the dialog footer
                label: 'check me', // Checkbox label
                caption: 'check me I\'magic', // Checkbox title
                className: 'my-checkbox', // Additional checkbox CSS class
                checked: true, // Default checkbox state
            },
            defaultButton: 0, // Index of the default button
            focusNodeSelector: '.my-input', // Selector for focussing an input element when dialog opens
            hasClose: false, // Whether to display a close button or not
            renderer: undefined // To define customized dialog structure


            source: https://jupyterlab.readthedocs.io/en/stable/extension/ui_helpers.html#generic-dialog
        """

        return self.app.schedule_operation(
            "showDialog", title=pack(title), body=pack(body), host=pack(host), **kwgs
        )

    def show_error_message(
        self, title: str, error: str, buttons: None | list[dict[str, str]] = None
    ) -> asyncio.Task:
        """Jupyter error message.

        buttons = [
            {
                "ariaLabel": "Accept error",
                "label": "Okay",
                "iconClass": "",
                "iconLabel": "",
                "caption": "",
                "className": 'error-circle',
                "accept": False,
                "actions": [],
                "displayType": "warn",
            }
        ]

        https://jupyterlab.readthedocs.io/en/stable/api/functions/apputils.showErrorMessage.html#showErrorMessage
        """
        return self.app.schedule_operation(
            "showErrorMessage", title=title, error=error, buttons=buttons
        )
