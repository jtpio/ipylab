// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { VBoxModel } from '@jupyter-widgets/controls';

import { MODULE_NAME, MODULE_VERSION } from '../version';

/**
 * The model for a panel.
 */
export class PanelModel extends VBoxModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PanelModel.model_name,
      _model_module: PanelModel.model_module,
      _model_module_version: PanelModel.model_module_version,
    };
  }

  static model_name = 'PanelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}
