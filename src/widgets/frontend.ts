// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// import { unpack_models } from '@jupyter-widgets/base';
import {
  DOMUtils,
  InputDialog,
  MainAreaWidget,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { FileDialog } from '@jupyterlab/filebrowser';
import { Session } from '@jupyterlab/services';
import {
  IDisposable,
  ISerializers,
  IpylabModel,
  JSONValue,
  JupyterFrontEnd,
  Widget
} from './ipylab';
import { newNotebook, newSessionContext } from './utils';
/**
 * The model for a JupyterFrontEnd.
 */
export class JupyterFrontEndModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name
    };
  }

  /**
   * Initialize a JupyterFrontEndModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this.set('version', this.app.version);
    Private.jupyterFrontEndModels.set(this.kernelId, this);

    this.sessionManager.runningChanged.connect(
      this._updateAllSessionDetails,
      this
    );
    if (this.labShell) {
      this.labShell.currentChanged.connect(this._updateSessionDetails, this);
      this.labShell.activeChanged.connect(this._updateSessionDetails, this);
      this._updateSessionDetails();
    }
    this._updateAllSessionDetails();
  }

  close(comm_closed?: boolean): Promise<void> {
    Private.jupyterFrontEndModels.delete(this.kernelId);
    this.labShell.currentChanged.disconnect(this._updateSessionDetails, this);
    this.labShell.activeChanged.disconnect(this._updateSessionDetails, this);
    this.sessionManager.runningChanged.disconnect(
      this._updateAllSessionDetails,
      this
    );
    return super.close(comm_closed);
  }

  get shell(): JupyterFrontEnd.IShell {
    return IpylabModel.app.shell;
  }

  get sessionManager(): Session.IManager {
    return IpylabModel.app.serviceManager.sessions;
  }

  private _updateSessionDetails(): void {
    const currentWidget = this.shell.currentWidget as any;
    const current_session = currentWidget?.sessionContext?.session?.model ?? {};
    if (this.get('current_widget_id') !== currentWidget?.id) {
      this.set('current_widget_id', currentWidget?.id ?? '');
      this.set('current_session', current_session);
      this.save_changes();
    }
  }
  private _updateAllSessionDetails(): void {
    this.set('all_sessions', Array.from(this.sessionManager.running()));
    this.save_changes();
  }

  async operation(op: string, payload: any): Promise<JSONValue | IDisposable> {
    function _get_result(result: any): any {
      if (result.value === null) {
        throw new Error('Cancelled');
      }
      return result.value;
    }
    let result, jfem: any;
    switch (op) {
      case 'addToShell':
        return await this._addToShell(payload);
      case 'showDialog':
        result = await showDialog(payload);
        return { value: result.button.accept, isChecked: result.isChecked };
      case 'getBoolean':
        return await InputDialog.getBoolean(payload).then(_get_result);
      case 'getItem':
        return await InputDialog.getItem(payload).then(_get_result);
      case 'getNumber':
        return await InputDialog.getNumber(payload).then(_get_result);
      case 'getText':
        return await InputDialog.getText(payload).then(_get_result);
      case 'getPassword':
        return await InputDialog.getPassword(payload).then(_get_result);
      case 'showErrorMessage':
        await showErrorMessage(payload.title, payload.error, payload.buttons);
        return IpylabModel.OPERATION_DONE;
      case 'getOpenFiles':
        payload.manager = this.defaultBrowser.model.manager;
        return await FileDialog.getOpenFiles(payload).then(_get_result);
      case 'getExistingDirectory':
        payload.manager = this.defaultBrowser.model.manager;
        return await FileDialog.getExistingDirectory(payload).then(_get_result);
      case 'newSessionContext':
        return await newSessionContext(payload);
      case 'newNotebook':
        return await newNotebook(payload);
      case 'execEval':
        // Use the JupyterFrontEndModel associated with the kernel to execute the code
        jfem = await this.getJupyterFrontEndModel(payload);
        return await jfem.scheduleOperation('execEval', payload);
      case 'startIyplabPythonBackend':
        return (await IpylabModel.pythonBackend.checkStart(
          payload.restart ?? false
        )) as any;
      case 'shutdownKernel':
        if (payload.kernelId) {
          await this.commands.execute('kernelmenu:shutdown', {
            id: payload.kernelId ?? this.kernelId
          });
        } else {
          (this.widget_manager as any).kernel.shutdown();
        }
        return null;
      default:
        return await super.operation(op, payload);
    }
  }

  /**
   * Add a widget to the application shell
   *
   * @param payload The payload to add
   */
  private async _addToShell(payload: any): Promise<Widget> {
    const { widget, area, options } = payload;
    let luminoWidget = widget;
    if (
      area === 'main' &&
      (!(luminoWidget instanceof MainAreaWidget) ||
        typeof luminoWidget.title === 'undefined')
    ) {
      luminoWidget = new MainAreaWidget({
        content: luminoWidget as any
      }) as any;
      luminoWidget.node.removeChild(luminoWidget.toolbar.node);
    }
    if (!luminoWidget.id) {
      luminoWidget.id = DOMUtils.createDomID();
    }
    this.shell.add(luminoWidget as any, area, options);
    return luminoWidget;
  }

  /**
   * Obtain the instance of the JupyterFrontEndModel for the sessions kernel.
   * If kernelId is not provided, a new kernel is created.
   * @param payload
   * @returns
   */
  async getJupyterFrontEndModel(payload: any): Promise<JupyterFrontEndModel> {
    if (payload.kernelId) {
      if (Private.jupyterFrontEndModels.has(payload.kernelId)) {
        return Private.jupyterFrontEndModels.get(payload.kernelId);
      }
    }
    throw new Error(
      `A kernel does not exist for the kernelId= '${payload.kernelId}'`
    );
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';
}

/**
 * A namespace for private data
 */
namespace Private {
  export const jupyterFrontEndModels = new Map<string, JupyterFrontEndModel>();
}
