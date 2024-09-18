import { Session } from '@jupyterlab/services';
import { IpylabModel, IDisposable } from './ipylab';
import { newSessionContext } from './utils';
/**
 *  The Python backend that auto loads python side plugins using `pluggy` module.
 *
 */
export class PythonBackendModel {
  async checkStart(restart?: false) {
    if (!this._backendSession || this._backendSession.disposed) {
      const context = await newSessionContext({
        path: 'Ipylab backend',
        name: 'Ipylab backend',
        language: 'python3',
        code: 'import ipylab.scripts; ipylab.scripts.init_ipylab_backend()'
      });
      this._backendSession = context.session;
    }
    if (restart && this._command) {
      this._command.dispose();
    }
    // Add a command
    if (!this._command || this._command.isDisposed) {
      this._command = IpylabModel.app.commands.addCommand(
        PythonBackendModel.checkstart,
        {
          label: 'Ipylab check start Python backend',
          caption:
            'Start the Ipylab Python backend that will run registered autostart plugins.\n ' +
            ' in "pyproject.toml"  added entry for: \n' +
            '[project.entry-points.ipylab_backend] \n' +
            '\tmyproject = "myproject.pluginmodule"',

          execute: () => IpylabModel.pythonBackend.checkStart()
        }
      );
      if (this._palletItem) {
        this._palletItem.dispose();
      }
      this._palletItem = IpylabModel.palette.addItem({
        command: PythonBackendModel.checkstart,
        category: 'ipylab',
        rank: 500
      });
    }

    return this._backendSession.model;
  }
  static checkstart = 'ipylab:check-start-python-backend';
  private _command?: IDisposable;
  private _palletItem?: IDisposable;
  private _backendSession?: Session.ISessionConnection;
}
