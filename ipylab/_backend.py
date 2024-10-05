# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import asyncio

from traitlets import Unicode

from ipylab.asyncwidget import AsyncWidgetBase


class IpylabBackEnd(AsyncWidgetBase):
    """This class is provided to run plugins on a default kernel.

    It will be created by IpylabPythonKernel when the ipylab plugin is activated.
    Entry points are loaded:
     1. On initial launch.
     2. When the page is loaded/refreshed.
     3. When the workspace is updated.

    Include the following lines in a module to utilise.

    ``` toml
    # pyproject.toml
    [project.entry-points.ipylab:load]
        myplugin = "myproject.ipylab_plugin:myplugin"
    ```
    """

    # This class should not be subclassed or instantiated directly.
    SINGLETON = True
    _model_name = Unicode("IpylabBackendModel", help="Name of the model.", read_only=True).tag(sync=True)

    def on_frontend_init(self, content):
        super().on_frontend_init(content)

        async def _backend_ready():
            "Load entrypoints."
            coros = self.plugin_manager.hook.on_backend_ready(app=self.app)

            results = await asyncio.gather(*coros, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self.log.exception("An exception occurred loading backend entrypoints")
                    await self.app.dialog.show_error_message("Plugin failure", str(result))
            await self.schedule_operation("backend_ready")

        self.to_task(_backend_ready())
