// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import {
  JupyterFrontEndPlugin,
  JupyterFrontEnd,
  ILabShell,
  ILayoutRestorer
} from '@jupyterlab/application';

import { DOMUtils, WidgetTracker } from '@jupyterlab/apputils';

import { IJupyterWidgetRegistry } from '@jupyter-widgets/base';

import { Widget } from '@phosphor/widgets';

import * as widgetExports from './widget';

import { MODULE_NAME, MODULE_VERSION } from './version';

const EXTENSION_ID = 'ipylab:plugin';

const extension: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  autoStart: true,
  requires: [IJupyterWidgetRegistry, ILabShell],
  optional: [ILayoutRestorer],
  activate: (
    app: JupyterFrontEnd,
    registry: IJupyterWidgetRegistry,
    shell: ILabShell,
    restorer: ILayoutRestorer | null
  ): void => {
    // create a single tracker for all the widgets
    const tracker = new WidgetTracker<Widget>({
      namespace: 'ipylab'
    });

    // add globals
    widgetExports.JupyterFrontEndModel._app = app;
    widgetExports.ShellModel._shell = shell;
    widgetExports.ShellModel._tracker = tracker;
    widgetExports.ShellModel._commands = app.commands;
    widgetExports.CommandRegistryModel._commands = app.commands;

    registry.registerWidget({
      name: MODULE_NAME,
      version: MODULE_VERSION,
      exports: widgetExports
    });

    app.commands.addCommand('ipylab:test', {
      execute: async args => {
        console.log('fsdfsdf');
        const widget = new Widget();
        const id = (args['id'] as string) || DOMUtils.createDomID();
        widget.id = id;
        void tracker.add(widget);
        shell.add(widget, 'main');
      }
    });

    if (restorer) {
      void restorer.restore(tracker, {
        args: widget => ({ id: widget.id }),
        name: widget => widget.id,
        command: 'ipylab:test'
      });
    }

    const sessions = app.serviceManager.sessions;
    console.log(sessions);
  }
};

export default extension;
