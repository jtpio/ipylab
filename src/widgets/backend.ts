// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ISessionContext } from '@jupyterlab/apputils';
import { UUID } from '@lumino/coreutils';
import { IDisposable, IpylabModel } from './ipylab';
import { newSessionContext } from './utils';
/**
 * The model to run in the backend for loading plugins.
 */
export class IpylabBackendModel extends IpylabModel {
  async operation(op: string, payload: any): Promise<any> {
    switch (op) {
      case 'backend_ready':
        return IpylabModel.backend_ready.resolve(null);
      default:
        return await super.operation(op, payload);
    }
  }

  static async checkStart(restart?: false) {
    // TODO: Make this a singleton and maybe don't need to subclass widget model (on the backend)
    if (
      !IpylabBackendModel.sessionContext ||
      IpylabBackendModel.sessionContext?.session === null ||
      restart
    ) {
      const path = 'Ipylab backend';
      await IpylabModel.sessionManager.refreshRunning();
      if (restart) {
        await IpylabBackendModel.sessionContext?.session?.kernel?.shutdown();
      }
      const model = await IpylabModel.sessionManager.findByPath(path);
      IpylabBackendModel.sessionContext = await newSessionContext({
        path: path,
        name: path,
        language: 'python3',
        kernelId: model ? null : UUID.uuid4(),
        code: 'import ipylab._backend; ipylab._backend.IpylabBackEnd()'
      });
    }
    if (restart && IpylabBackendModel._command) {
      IpylabBackendModel._command.dispose();
    }
    // Add a command
    if (
      !IpylabBackendModel._command ||
      IpylabBackendModel._command.isDisposed
    ) {
      IpylabBackendModel._command = IpylabModel.app.commands.addCommand(
        IpylabBackendModel.checkstart,
        {
          label: 'Ipylab check start Python backend',
          caption:
            'Start the Ipylab Python backend that will run registered autostart plugins.\n ' +
            ' in "pyproject.toml"  added entry for: \n' +
            '[project.entry-points.ipylab_autostart] \n' +
            '\tmyproject = "myproject.pluginmodule"',

          execute: () => IpylabBackendModel.checkStart()
        }
      );
      if (IpylabBackendModel._palletItem) {
        IpylabBackendModel._palletItem.dispose();
      }
      IpylabBackendModel._palletItem = IpylabModel.palette.addItem({
        command: IpylabBackendModel.checkstart,
        category: 'ipylab',
        rank: 500
      });
    }
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: IpylabBackendModel.model_name
    };
  }
  static model_name = 'IpylabBackendModel';
  static checkstart = 'ipylab:check-start-python-backend';
  static _command?: IDisposable;
  static _palletItem?: IDisposable;
  static sessionContext?: ISessionContext;
}
