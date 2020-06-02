// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { WidgetModel } from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';

/**
 * The model for a title widget.
 */
export class TitleModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: TitleModel.model_name,
      _model_module: TitleModel.model_module,
      _model_module_version: TitleModel.model_module_version,
    };
  }

  static model_name = 'TitleModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;
}
