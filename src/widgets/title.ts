// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { WidgetModel, unpack_models } from '@jupyter-widgets/base';

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

  /**
   * Initialize a LabIcon instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this.on('change:icon', this.iconChanged);
  }

  /**
   * Pass on changes from the icon.
   */
  async iconChanged() {
    const icon = await unpack_models(this.get('icon'), this.widget_manager);
    if (icon) {
      icon.on('change', () => this.trigger('change'));
    }
  }

  static model_name = 'TitleModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;
}
