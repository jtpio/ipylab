import { ISessionContext, SessionContext } from '@jupyterlab/apputils';

import { IOutput } from '@jupyterlab/nbformat';

import { Kernel, KernelMessage } from '@jupyterlab/services';

import { ISignal, Signal } from '@lumino/signaling';

import { ServiceManager } from '@jupyterlab/services';

import { ITranslator } from '@jupyterlab/translation';

/**
 *  The python backend that manages python side plugins.
 */
export class PythonBackendModel {
  async checkStart(manager: ServiceManager.IManager, translator: ITranslator) {
    if (!this._sessionContext || this._sessionContext.isDisposed) {
      this._sessionContext = new SessionContext({
        sessionManager: manager.sessions,
        specsManager: manager.kernelspecs,
        name: 'Ipylab backend',
        translator: translator,
        kernelPreference: {
          autoStartDefault: true,
          canStart: true,
          shouldStart: true,
          language: 'python'
        }
      });
    }
    await this._sessionContext.initialize();
    await this._sessionContext.ready;
    this.execute('import ipylab.scripts; ipylab.scripts.init_ipylab_backend()');
    const result = await this.future.done;
    result;
  }

  get future(): Kernel.IFuture<
    KernelMessage.IExecuteRequestMsg,
    KernelMessage.IExecuteReplyMsg
  > | null {
    return this._future;
  }

  set future(
    value: Kernel.IFuture<
      KernelMessage.IExecuteRequestMsg,
      KernelMessage.IExecuteReplyMsg
    > | null
  ) {
    this._future = value;
    if (!value) {
      return;
    }
    value.onIOPub = this._onIOPub;
  }

  get output(): IOutput | null {
    return this._output;
  }

  get stateChanged(): ISignal<PythonBackendModel, void> {
    return this._stateChanged;
  }

  execute(code: string): void {
    if (!this._sessionContext || !this._sessionContext.session?.kernel) {
      return;
    }
    this.future = this._sessionContext.session?.kernel?.requestExecute({
      code,
      store_history: false
    });
  }

  private _onIOPub = (msg: KernelMessage.IIOPubMessage): void => {
    const msgType = msg.header.msg_type;
    switch (msgType) {
      case 'execute_result':
      case 'display_data':
      case 'update_display_data':
        this._output = msg.content as IOutput;
        console.log(this._output);
        this._stateChanged.emit();
        break;
      default:
        break;
    }
    return;
  };

  private _future: Kernel.IFuture<
    KernelMessage.IExecuteRequestMsg,
    KernelMessage.IExecuteReplyMsg
  > | null = null;
  private _output: IOutput | null = null;
  private _sessionContext: ISessionContext;
  private _stateChanged = new Signal<PythonBackendModel, void>(this);
}
