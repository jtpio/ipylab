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
                        k: getattr(model, k)
                        for k in model.class_trait_names()
                        if not (
                            k.startswith("_") or k == "error" or k in Widget._traits
                        )
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
    _syncing: t.Optional[bool]

    error = Unicode(allow_none=True)

    name = Unicode(allow_none=True)
    path = Unicode(allow_none=True).tag(sync=True)
    last_modified = Unicode(allow_none=True)
    created = Unicode(allow_none=True)
    format = Unicode(allow_none=True)
    mimetype = Unicode(allow_none=True)
    size = Int(allow_none=True)
    writeable = Bool(allow_none=True)
    type = Unicode(allow_none=True)
    content = Any(allow_none=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observe(self._on_content, "content")

    def _on_get(self, msg):
        if "error" in msg:
            self.error = msg["error"]
            return
        func = msg.get("func")
        self._syncing = True
        for key, value in msg.get("model", {}).items():
            if func == "save" and key == "content":
                continue
            setattr(self, key, value)
        self._syncing = False

    def _on_content(self, change) -> None:
        if self._syncing:
            return
        self._contents_manager.save(self)
