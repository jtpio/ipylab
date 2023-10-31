#!/usr/bin/env python
# coding: utf-8

# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import typing as t
from uuid import uuid4
from ipywidgets import Widget, register
from traitlets import HasTraits, Unicode, Any, Instance, observe, Int, Bool
from ._frontend import module_name, module_version


@register
class ContentsManager(Widget):
    _model_name = Unicode("ContentsManagerModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    _requests: t.Dict[str, t.Callable]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._requests = {}
        self.on_msg(self._on_frontend_msg)

    def _on_frontend_msg(self, _, content, buffers):
        if content.get("event", "") == "got":
            _id = content.get("_id")
            callback = self._requests.pop(_id, None)
            if callback:
                callback(content)

    def get(self, path: str, content: t.Optional[bool] = None) -> "ContentsModel":
        _id = str(uuid4())
        self.send(
            {
                "_id": _id,
                "func": "get",
                "payload": {"path": path, "options": {"content": content}},
            }
        )

        model = ContentsModel(path=path, _contents_manager=self)

        self._requests[_id] = model._on_get

        return model

    def save(self, model: "ContentsModel"):
        _id = str(uuid4())
        self.send(
            {
                "_id": _id,
                "func": "save",
                "payload": {
                    "path": model.path,
                    "options": {
                        "content": model.content,
                        "type": model.type,
                        "format": model.format,
                    },
                },
            }
        )

        self._requests[_id] = model._on_get

        return model


@register
class ContentsModel(Widget):
    _model_name = Unicode("ContentsModelModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _contents_manager = Instance(ContentsManager)

    name = Unicode()
    path = Unicode()
    last_modified = Unicode()
    created = Unicode()
    format = Unicode()
    mimetype = Unicode()
    size = Int()
    writeable = Bool()
    type = Unicode()
    content = Any()

    def _on_get(self, content):
        with self.hold_trait_notifications():
            for key, value in content.get("model", {}).items():
                setattr(self, key, value)

    @observe("content")
    def _on_content(self, change) -> None:
        self._contents_manager.save(self)
