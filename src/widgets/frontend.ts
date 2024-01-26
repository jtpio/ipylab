// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import {
  DOMUtils,
  InputDialog,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { FileDialog } from '@jupyterlab/filebrowser';
import {
  ISerializers,
  IpylabModel,
  JSONValue,
  JupyterFrontEnd
} from './ipylab';
import { IpylabMainAreaWidget } from './main_area';
import { LabShell } from '@jupyterlab/application';

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
    this.save_changes();
  }

  get shell(): JupyterFrontEnd.IShell {
    return IpylabModel.app.shell;
  }
  get labShell(): LabShell {
    return IpylabModel.labShell;
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    function _get_result(result: any): any {
      if (result.value === null) throw new Error('Cancelled');
      return result.value;
    }
    var result: any;
    switch (op) {
      case 'addToShell':
        return await this._addToShell(payload);
      case 'showDialog':
        result = await showDialog(payload);
        4;
        return { value: result.button.accept, isChecked: result.isChecked };
      case 'getBoolean':
        return await InputDialog.getBoolean(payload).then(_get_result);
      case 'getItem':
        return await InputDialog.getItem(payload).then(_get_result);
      case 'getNumber':
        return await InputDialog.getNumber(payload).then(_get_result);
      case `getText`:
        return await InputDialog.getText(payload).then(_get_result);
      case `getPassword`:
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
    var luminoWidget = view.luminoWidget;
    if (area === 'main') {
      luminoWidget = new IpylabMainAreaWidget({
        content: view.luminoWidget,
        kernel_id: this.get('kernel_id'),
        name: 'Ipylab'
      });
    }
    if (!luminoWidget.id) luminoWidget.id = DOMUtils.createDomID();
    this.shell.add(luminoWidget, area, options);
    model.on('comm_live_update', () => {
      if (!model.comm_live) luminoWidget.close();
    });
    return luminoWidget.id;
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';
}
