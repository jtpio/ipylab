// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
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
    this._app = JupyterFrontEndModel.app;
    super.initialize(attributes, options);
    this.set('version', this._app.version);
    this.save_changes();
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    function _get_result(result: any): any {
      if (result.value === null) throw new Error('Cancelled');
      return result.value;
    }
    var result: any;
    switch (op) {
      case `showDialog`:
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
        return 'done';
      case 'getOpenFiles':
        payload.manager = IpylabModel.defaultBrowser.model.manager;
        result = await FileDialog.getOpenFiles(payload);
        return result.value;
      case 'getExistingDirectory':
        payload.manager = IpylabModel.defaultBrowser.model.manager;
        result = await FileDialog.getExistingDirectory(payload);
        return result.value;
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${JupyterFrontEndModel.model_name}!`
        );
    }
  }
  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';

  private _app!: JupyterFrontEnd;
}
