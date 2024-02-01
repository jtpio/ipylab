// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { WidgetModel, unpack_models } from '@jupyter-widgets/base';
import { Title } from '@lumino/widgets';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { IconModel } from './icon';

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
      _model_module_version: TitleModel.model_module_version
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
    this.on('change:icon', this._iconChanged);
  }

  /**
   * Load settings into the widget
   * @param luminoWidget
   */
  update_title(title: Title<any>) {
    title.caption = this.get('caption');
    title.className = this.get('class_name');
    title.closable = this.get('closable');
    title.label = this.get('label');
    title.dataset = this.get('dataset');
    title.iconLabel = this.get('icon_label');

    const icon = this.get('icon');
    title.icon = icon ? icon.labIcon : null;
    title.iconClass = icon ? null : this.get('icon_class');
  }

  // /**
  //  * Pass on changes from the icon.
  //  */
  private _iconChanged() {
    const icon = this.get('icon');
    this.listenTo(icon, 'change', () => {
      // Pass on changes from the icon.
      this.trigger('change');
    });
  }

  static serializers = {
    icon: { deserialize: unpack_models }
  };
  icon: IconModel;
  static model_name = 'TitleModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_module_version = MODULE_VERSION;
}
