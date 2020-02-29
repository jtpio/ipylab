// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { JupyterPhosphorWidget, DOMWidgetView } from '@jupyter-widgets/base';

import { VBoxView } from '@jupyter-widgets/controls';

import { Message } from '@lumino/messaging';

import { SplitPanel } from '@lumino/widgets';

import $ from 'jquery';

import { PanelModel } from './panel';

import { MODULE_NAME, MODULE_VERSION } from '../version';

class JupyterLuminoSplitPanelWidget extends SplitPanel {
  constructor(options: JupyterPhosphorWidget.IOptions & SplitPanel.IOptions) {
    let view = options.view;
    delete options.view;
    super(options);
    this.addClass('jp-JupyterLuminoSplitPanelWidget');
    this._view = view;
  }

  processMessage(msg: Message) {
    super.processMessage(msg);
    this._view.processPhosphorMessage(msg);
  }

  dispose() {
    if (this.isDisposed) {
      return;
    }
    super.dispose();
    if (this._view) {
      this._view.remove();
    }
    this._view = null;
  }

  private _view: DOMWidgetView;
}

export class SplitPanelModel extends PanelModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: SplitPanelModel.model_name,
      _model_module: SplitPanelModel.model_module,
      _model_module_version: SplitPanelModel.model_module_version,
      _view_name: SplitPanelModel.model_name,
      _view_module: SplitPanelModel.model_module,
      _view_module_version: SplitPanelModel.model_module_version
    };
  }

  static model_name = 'SplitPanelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'SplitPanelView';
  static view_module = MODULE_NAME;
  static view_module_name = MODULE_VERSION;
}

export class SplitPanelView extends VBoxView {
  _createElement(tagName: string) {
    this.pWidget = new JupyterLuminoSplitPanelWidget({
      view: this,
      orientation: this.model.get('orientation')
    }) as any;
    return this.pWidget.node;
  }

  _setElement(el: HTMLElement) {
    if (this.el || el !== this.pWidget.node) {
      throw new Error('Cannot reset the DOM element.');
    }

    this.el = this.pWidget.node;
    this.$el = $(this.pWidget.node);
  }

  initialize(parameters: any) {
    super.initialize(parameters);
    const pWidget = (this.pWidget as any) as JupyterLuminoSplitPanelWidget;
    this.model.on('change:orientation', () => {
      const orientation = this.model.get('orientation');
      pWidget.orientation = orientation;
    });
  }

  async render() {
    super.render();
    const views = await Promise.all(this.children_views.views);
    views.forEach(async (view: DOMWidgetView) => {
      this.pWidget.addWidget(view.pWidget);
    });
  }
}
