import {
  JupyterFrontEndPlugin,
  JupyterFrontEnd,
  ILabShell,
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { IJupyterWidgetRegistry } from '@jupyter-widgets/base';

import * as widgetExports from './widget';

import { MODULE_NAME, MODULE_VERSION } from './version';

const EXTENSION_ID = 'ipyfbl:plugin';

/**
 * The default plugin.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  autoStart: true,
  requires: [IJupyterWidgetRegistry, ILabShell],
  optional: [ICommandPalette],
  activate: (
    app: JupyterFrontEnd,
    registry: IJupyterWidgetRegistry,
    shell: ILabShell,
    palette: ICommandPalette
  ): void => {
    // add globals
    widgetExports.JupyterFrontEndModel.app = app;
    widgetExports.ShellModel.shell = shell;
    widgetExports.CommandRegistryModel.commands = app.commands;
    widgetExports.SessionManagerModel.sessions = app.serviceManager.sessions;
    widgetExports.SessionManagerModel.shell = shell;

    registry.registerWidget({
      name: MODULE_NAME,
      version: MODULE_VERSION,
      exports: widgetExports,
    });
  },
};

export default extension;
