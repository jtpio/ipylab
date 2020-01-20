// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { VBoxModel } from '@jupyter-widgets/controls';

import { MODULE_NAME, MODULE_VERSION } from '../version';

export class PanelModel extends VBoxModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: PanelModel.model_name,
      _model_module: PanelModel.model_module,
      _model_module_version: PanelModel.model_module_version,
      _view_name: null
    };
  }

  static model_name = 'PanelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}
