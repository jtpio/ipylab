// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  ILabShell,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { IJupyterWidgetRegistry } from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';

const EXTENSION_ID = 'ipylab:plugin';

/**
 * The default plugin.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  autoStart: true,
  requires: [IJupyterWidgetRegistry],
  optional: [ICommandPalette, ILabShell, IDefaultFileBrowser],
  activate: async (
    app: JupyterFrontEnd,
    registry: IJupyterWidgetRegistry,
    palette: ICommandPalette,
    labShell: ILabShell | null,
    defaultBrowser: IDefaultFileBrowser | null
  ) => {
    const widgetExports = await import('./widget');
    if (!widgetExports.JupyterFrontEndModel.app) {
      // add globals
      widgetExports.IpylabModel.app = app;
      widgetExports.IpylabModel.labShell = labShell;
      widgetExports.IpylabModel.defaultBrowser = defaultBrowser;
      widgetExports.IpylabModel.palette = palette;

      registry.registerWidget({
        name: MODULE_NAME,
        version: MODULE_VERSION,
        exports: widgetExports
      });
    }
    // TODO: Start the core kernel that will provide the launchers
  }
};

export default extension;
