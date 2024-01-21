// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  ILabShell,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { IJupyterWidgetRegistry } from '@jupyter-widgets/base';

import { ILauncher } from '@jupyterlab/launcher';

import { ITranslator } from '@jupyterlab/translation';

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
  optional: [
    ICommandPalette,
    ILabShell,
    IDefaultFileBrowser,
    ILauncher,
    ITranslator
  ],
  activate: activate
};

/**
 * Activate the JupyterLab extension.
 *
 * @param app Jupyter Front End
 * @param registry Jupyter Widget Registry
 * @param palette Jupyter Commands
 * @param labShell Jupyter Shell
 * @param defaultBrowser Jupyter Default File Brower
 * @param launcher [optional] Jupyter Launcher
 * @param translator Jupyter Translator
 */
async function activate(
  app: JupyterFrontEnd,
  registry: IJupyterWidgetRegistry,
  palette: ICommandPalette,
  labShell: ILabShell | null,
  defaultBrowser: IDefaultFileBrowser | null,
  launcher: ILauncher | null,
  translator: ITranslator | null
) {
  const widgetExports = await import('./widget');
  if (!widgetExports.JupyterFrontEndModel.app) {
    // add globals
    widgetExports.IpylabModel.app = app;
    widgetExports.IpylabModel.labShell = labShell;
    widgetExports.IpylabModel.defaultBrowser = defaultBrowser;
    widgetExports.IpylabModel.palette = palette;
    widgetExports.IpylabModel.translator = translator;
    widgetExports.IpylabModel.launcher = launcher;

    registry.registerWidget({
      name: MODULE_NAME,
      version: MODULE_VERSION,
      exports: widgetExports
    });
  }
  widgetExports.IpylabModel.python_backend.checkStart(
    app.serviceManager,
    translator
  );
}

export default extension;
