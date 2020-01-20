// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { JupyterFrontEnd } from '@jupyterlab/application';

import {
  DOMWidgetModel,
  ISerializers,
  WidgetModel
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';

export class JupyterFrontEndModel extends WidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name,
      _model_module: JupyterFrontEndModel.model_module,
      _model_module_version: JupyterFrontEndModel.model_module_version
    };
  }

  initialize(attributes: any, options: any) {
    this.app = JupyterFrontEndModel._app;
    super.initialize(attributes, options);
    this.send({ event: 'lab_ready' }, {});
    this.set('version', this.app.version);
    this.save_changes();
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private app: JupyterFrontEnd;
  static _app: JupyterFrontEnd;
}
