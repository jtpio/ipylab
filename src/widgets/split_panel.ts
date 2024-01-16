// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { Message } from '@lumino/messaging';

import { SplitPanel } from '@lumino/widgets';

import { PanelModel, PanelView } from './panel';

export declare namespace JupyterLuminoSplitPanelWidget {
  interface IOptions {
    view: SplitPanelView;
  }
}

/**
 * A Lumino widget for split panels.
 */
class JupyterLuminoSplitPanelWidget extends SplitPanel {
  /**
   * Construct a new JupyterLuminoSplitPanelWidget.
   *
   * @param options The instantiation options for a JupyterLuminoSplitPanelWidget.
   */
  constructor(
    options: JupyterLuminoSplitPanelWidget.IOptions & SplitPanel.IOptions
  ) {
    const view = options.view;
    delete (options as any).view;
    super(options);
    this._view = view;
  }

  /**
   * Process the Lumino message.
   *
   * Any custom Lumino widget used inside a Jupyter widget should override
   * the processMessage function like this.
   */
  processMessage(msg: Message): void {
    super.processMessage(msg);
    this._view.processLuminoMessage(msg);
  }

  /**
   * Dispose the widget.
   *
   * This causes the view to be destroyed as well with 'remove'
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    super.dispose();
    this._view?.remove();
    this._view = null!;
  }

  private _view: SplitPanelView;
}

/**
 * The model for a split panel.
 */
export class SplitPanelModel extends PanelModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SplitPanelModel.model_name,
      _model_module: SplitPanelModel.model_module,
      _model_module_version: SplitPanelModel.model_module_version,
      _view_name: SplitPanelModel.view_name,
      _view_module: SplitPanelModel.model_module,
      _view_module_version: SplitPanelModel.model_module_version
    };
  }

  static model_name = 'SplitPanelModel';
  static view_name = 'SplitPanelView';
  class_name = 'ipylab-splitpanel';
}

/**
 * The view for a split panel.
 */
export class SplitPanelView extends PanelView {
  /**
   * Create the widget and return the DOM element.
   *
   * @param tagName the tag name
   */
  _createElement(tagName: string): HTMLElement {
    this.luminoWidget = new JupyterLuminoSplitPanelWidget({
      view: this
    }) as any;
    return this.luminoWidget.node;
  }

  /**
   * Render the view.
   */
  render() {
    super.render();
    this.update_luminoWidget();
    this.listenTo(this.model, 'change:orientation', this.update_luminoWidget);
  }

  update_luminoWidget() {
    const luminoWidget = this
      .luminoWidget as any as JupyterLuminoSplitPanelWidget;
    luminoWidget.orientation = this.model.get('orientation');
  }
}
