# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import ipylab


class HasApp:
    @property
    def app(self) -> ipylab.JupyterFrontEnd:
        if not hasattr(self, "_app"):
            self._app = ipylab.JupyterFrontEnd()
        return self._app
