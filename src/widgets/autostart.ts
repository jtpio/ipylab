// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ISessionContext } from '@jupyterlab/apputils';
import { UUID } from '@lumino/coreutils';
import { IDisposable, IpylabModel } from './ipylab';
/**
 * The model to run in the Ipylab kernel.
 */
export class IpylabAutostart {
  static async checkStart(restart = false) {
    if (
      !IpylabAutostart.sessionContext ||
      IpylabAutostart.sessionContext?.session === null ||
      restart
    ) {
      const path = 'Ipylab';
      await IpylabModel.sessionManager.refreshRunning();
      if (restart) {
        await IpylabAutostart.sessionContext?.session?.kernel?.shutdown();
      }
      const model = await IpylabModel.sessionManager.findByPath(path);
      IpylabAutostart.sessionContext = await IpylabModel.newSessionContext({
        path: path,
        name: path,
        language: 'python',
        kernelId: model ? null : UUID.uuid4(),
        ensureFrontend: 'isIpylabKernel'
      });
    }
    if (restart && IpylabAutostart._command) {
      IpylabAutostart._command.dispose();
    }
    // Add a command
    if (!IpylabAutostart._command || IpylabAutostart._command.isDisposed) {
      IpylabAutostart._command = IpylabModel.app.commands.addCommand(
        IpylabAutostart.checkstart,
        {
          label: 'Ipylab restart default kernel',
          caption: 'Start or restart the default Ipylab Kernel.',
          execute: () => IpylabAutostart.checkStart(true)
        }
      );
      if (IpylabAutostart._palletItem) {
        IpylabAutostart._palletItem.dispose();
      }
      IpylabAutostart._palletItem = IpylabModel.palette.addItem({
        command: IpylabAutostart.checkstart,
        category: 'ipylab',
        rank: 500
      });
    }
  }

  static checkstart = 'ipylab:autostart';
  static _command?: IDisposable;
  static _palletItem?: IDisposable;
  static sessionContext?: ISessionContext;
}
