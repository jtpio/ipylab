# Copyright (c) Jeremy Tuloup.
# Distributed under the terms of the Modified BSD License.

import asyncio

from uuid import uuid4


class Awaitable:
    def __init__(self, *args, **kwargs):
        self._futures = {}

    def _on_frontend_msg(self, _, content, buffers):
        if content.get("event", "") == "future":
            future_id = content.get("future_id")
            result = content.get("result", None)
            if future_id in self._futures:
                self._futures[future_id].set_result(result)
                del self._futures[future_id]

    def register_future(self):
        future_id = uuid4().hex
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._futures[future_id] = fut
        return future_id, fut
