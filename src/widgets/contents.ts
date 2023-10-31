// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { WidgetModel } from '@jupyter-widgets/base';
import { Contents } from '@jupyterlab/services';

import { MODULE_NAME, MODULE_VERSION } from '../version';

export class ContentsManagerModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ContentsManagerModel.model_name,
      _model_module: ContentsManagerModel.model_module,
      _model_module_version: ContentsManagerModel.model_module_version
    };
  }

  /**
   * Initialize a ContentsManagerModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private async _onMessage(msg: any): Promise<void> {
    switch (msg.func) {
      case 'get':
        void this._get(msg._id, msg.payload);
        break;
      case 'save':
        void this._save(msg._id, msg.payload);
        break;
      default:
        break;
    }
  }

  private async _get(
    _id: string,
    payload: { path: string; options: Record<string, any> }
  ) {
    const model = await ContentsManagerModel.contentsManager.get(
      payload.path,
      payload.options
    );
    this.send({ event: 'got', _id, model: model as any });
  }

  private async _save(
    _id: string,
    payload: { path: string; options: Record<string, any> }
  ) {
    const model = await ContentsManagerModel.contentsManager.save(
      payload.path,
      payload.options
    );
    this.send({ event: 'saved', _id, model: model as any });
  }

  static model_name = 'ContentsManagerModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  static contentsManager: Contents.IManager;
}

export class ContentsModelModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      contents: null,
      _model_name: ContentsModelModel.model_name,
      _model_module: ContentsModelModel.model_module,
      _model_module_version: ContentsModelModel.model_module_version
    };
  }

  static model_name = 'ContentsModelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;
}
