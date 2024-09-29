// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { DOMWidgetModel, DOMWidgetView } from '@jupyter-widgets/base';
import { LabIcon } from '@jupyterlab/ui-components';
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
        props: { tag: 'div' }
      });
    }
  }

  model!: IconModel;
  protected iconElement!: HTMLElement;
}

/**
 * The model for a title widget.
 */
export class IconModel extends DOMWidgetModel {
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
   * Update the LabIcon when model changes occur
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

  protected _labIcon!: LabIcon;

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: 'IconModel',
      _model_module: MODULE_NAME,
      _model_module_version: MODULE_VERSION,
      _view_name: 'IconView',
      _view_module: MODULE_NAME,
      _view_module_version: MODULE_VERSION
    };
  }
}
