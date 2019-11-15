// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import {
  JupyterFrontEndPlugin,
  JupyterFrontEnd
} from "@jupyterlab/application";

import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";

import * as widgetExports from "./widget";

import { MODULE_NAME, MODULE_VERSION } from "./version";

const EXTENSION_ID = "ipylab:plugin";

const extension: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  autoStart: true,
  requires: [IJupyterWidgetRegistry],
  activate: (app: JupyterFrontEnd, registry: IJupyterWidgetRegistry): void => {
    widgetExports.JupyterFrontEndModel._app = app;
    widgetExports.CommandRegistryModel._commands = app.commands;
    registry.registerWidget({
      name: MODULE_NAME,
      version: MODULE_VERSION,
      exports: widgetExports
    });
  }
};

export default extension;
