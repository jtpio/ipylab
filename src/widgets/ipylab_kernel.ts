import { SessionContext } from '@jupyterlab/apputils';
import { UUID } from '@lumino/coreutils';
import { IDisposable, IpylabModel } from './ipylab';
import { newSessionContext } from './utils';

/**
 *  The Python backend that auto loads python side plugins using `pluggy` module.
 *
 */
export class IpylabPythonKernel {
  async checkStart(restart?: false) {
    if (
      !this._backendSession ||
      this._backendSession?.session === null ||
      restart
    ) {
      if (restart) {
        await this._backendSession?.session.kernel.shutdown();
      }
      this._backendSession = await newSessionContext({
        path: 'Ipylab backend',
        name: 'Ipylab backend',
        language: 'python3',
        code: 'import ipylab.ipylab_backend; ipylab.ipylab_backend.IpylabBackEnd()',
        kernelId: UUID.uuid4()
      });
    }
    if (restart && this._command) {
      this._command.dispose();
    }
    // Add a command
    if (!this._command || this._command.isDisposed) {
      this._command = IpylabModel.app.commands.addCommand(
        IpylabPythonKernel.checkstart,
        {
          label: 'Ipylab check start Python backend',
          caption:
            'Start the Ipylab Python backend that will run registered autostart plugins.\n ' +
            ' in "pyproject.toml"  added entry for: \n' +
            '[project.entry-points.ipylab_autostart] \n' +
            '\tmyproject = "myproject.pluginmodule"',

          execute: () => IpylabModel.ipylabKernel.checkStart()
        }
      );
      if (this._palletItem) {
        this._palletItem.dispose();
      }
      this._palletItem = IpylabModel.palette.addItem({
        command: IpylabPythonKernel.checkstart,
        category: 'ipylab',
        rank: 500
      });
    }

    return this._backendSession.session.model;
  }
  static checkstart = 'ipylab:check-start-python-backend';
  private _command?: IDisposable;
  private _palletItem?: IDisposable;
  private _backendSession?: SessionContext;
}
