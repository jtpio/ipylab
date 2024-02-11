// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import { LabShell } from '@jupyterlab/application';
import {
  DOMUtils,
  InputDialog,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { FileDialog } from '@jupyterlab/filebrowser';
import { Session } from '@jupyterlab/services';
import {
  ISerializers,
  IpylabModel,
  JSONValue,
  JupyterFrontEnd
} from './ipylab';
import { IpylabMainAreaWidget } from './main_area';
import { injectCode, newNotebook, newSession, onKernelLost } from './utils';

/**
 * The model for a JupyterFrontEnd.
 */
export class JupyterFrontEndModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name,
      _model_module: JupyterFrontEndModel.model_module,
      _model_module_version: JupyterFrontEndModel.model_module_version
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
    this.save_changes();
  }

  get shell(): JupyterFrontEnd.IShell {
    return IpylabModel.app.shell;
  }
  get labShell(): LabShell {
    return IpylabModel.labShell;
  }

  get sessionManager(): Session.IManager {
    return IpylabModel.app.serviceManager.sessions;
  }

  private _updateSessionDetails(): void {
    const currentWidget = this.shell.currentWidget as any;
    const current_session = currentWidget?.sessionContext?.session?.model ?? {};
    this.set('current_widget_id', currentWidget?.id ?? '');
    this.set('current_session', current_session);
    this.save_changes();
  }
  private _updateAllSessionDetails(): void {
    this.set('all_sessions', Array.from(this.sessionManager.running()));
    this.save_changes();
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    function _get_result(result: any): any {
      if (result.value === null) {
        throw new Error('Cancelled');
      }
      return result.value;
    }
    let result: any;
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
        payload.manager = IpylabModel.defaultBrowser.model.manager;
        return await FileDialog.getOpenFiles(payload).then(_get_result);
      case 'getExistingDirectory':
        payload.manager = IpylabModel.defaultBrowser.model.manager;
        return await FileDialog.getExistingDirectory(payload).then(_get_result);
      case 'newSession':
        result = await newSession(payload);
        return result.model;
      case 'newNotebook':
        result = await newNotebook(payload);
        return result.sessionContext.session.model;
      case 'injectCode':
        return await injectCode(payload);
      case 'startIyplabPythonBackend':
        return (await IpylabModel.python_backend.checkStart()) as any;
      case 'shutdownKernel':
        if (payload.kernelId) {
          await IpylabModel.app.commands.execute('kernelmenu:shutdown', {
            id: payload.kernelId ?? this.kernelId
          });
        } else {
          (this.widget_manager as any).kernel.shutdown();
        }
        return null;
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${JupyterFrontEndModel.model_name}!`
        );
    }
  }

  /**
   * Add a widget to the application shell
   *
   * @param payload The payload to add
   */
  private async _addToShell(payload: any): Promise<JSONValue> {
    const { serializedWidget, area, options } = payload;
    const model = await unpack_models(serializedWidget, this.widget_manager);
    const view = await this.widget_manager.create_view(model, {});
    let luminoWidget = view.luminoWidget;
    if (area === 'main') {
      luminoWidget = new IpylabMainAreaWidget({
        content: view.luminoWidget,
        kernelId: this.kernelId,
        name: 'Ipylab'
      });
    }
    if (!luminoWidget.id) {
      luminoWidget.id = DOMUtils.createDomID();
    }
    this.shell.add(luminoWidget, area, options);
    onKernelLost(
      (this.widget_manager as any).kernel,
      luminoWidget.dispose,
      luminoWidget
    );
    return { id: luminoWidget.id };
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';
}
