# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from ipylab.asyncwidget import AsyncWidgetBase
from ipylab.hasapp import HasApp
from ipylab.hookspecs import pm


class IpylabBackEnd(AsyncWidgetBase, HasApp):
    """This class is provided to load `ipylab_autostart` entypoints.

    It will be created by IpylabPythonKernel when the ipylab plugin is activated.

    Include the following lines in a module to utilise.

    ``` toml
    # pyproject.toml
    [project.entry-points.ipylab_autostart]
        myproject = "myproject.pluginmodule"

    ```
    """

    SINGLETON = True

    def _load_ipylab_backend_entrypoints(self):
        "Load entrypoints."
        try:
            count = pm.load_setuptools_entrypoints("ipylab_autostart")
            self.log.info("Ipylab python backend found {%} plugin entry points.", count)
        except Exception as e:
            self.log.exception("An exception occurred loading backend entrypoints")
            self.app.dialog.show_error_message("Plugin failure", str(e))

    def on_frontend_init(self, content):
        super().on_frontend_init(content)
        self._load_ipylab_backend_entrypoints()
