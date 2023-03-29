// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { LabIcon } from '@jupyterlab/ui-components';

import { DOMWidgetView, DOMWidgetModel } from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';

export class IconView extends DOMWidgetView {
  initialize(parameters: any) {
    super.initialize(parameters);
    this.iconElement = document.createElement('div');
    this.el.appendChild(this.iconElement);
    this.update();
  }

  update() {
    const { labIcon } = this.model;
    if (labIcon) {
      labIcon.render(this.iconElement, {
        props: { tag: 'div' },
      });
    }
  }

  model: IconModel;
  protected iconElement: HTMLElement;
}

/**
 * The model for a title widget.
 */
export class IconModel extends DOMWidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: IconModel.model_name,
      _model_module: IconModel.model_module,
      _model_module_version: IconModel.model_module_version,
      _view_name: IconModel.view_name,
      _view_module: IconModel.view_module,
      _view_module_version: IconModel.view_module_version,
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
    this.on('change:name change:svgstr', this.updateIcon);
    this.updateIcon();
  }

  get labIcon(): LabIcon {
    return this._labIcon;
  }

  /**
   * Update the LabIcon when model chenges occur
   */
  updateIcon() {
    const name = this.get('name');
    const svgstr = this.get('svgstr');
    if (!this._labIcon || this._labIcon.name !== name) {
      this._labIcon = new LabIcon({ name, svgstr });
    }
    this._labIcon.svgstr = svgstr;
    this.trigger('change');
  }

  protected _labIcon: LabIcon;

  static model_name = 'IconModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'IconView';
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;
}
