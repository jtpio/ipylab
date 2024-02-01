// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  IBackboneModelOptions,
  JupyterLuminoPanelWidget,
  WidgetView,
  unpack_models
} from '@jupyter-widgets/base';
import { BoxModel, BoxView } from '@jupyter-widgets/controls';
import { ObjectHash } from 'backbone';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { TitleModel } from '../widgets/title';

/**
 * The model for a panel.
 */
export class PanelModel extends BoxModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: PanelModel.model_name,
      _model_module: PanelModel.model_module,
      _model_module_version: PanelModel.model_module_version,
      _view_name: PanelModel.view_name,
      _view_module: PanelModel.model_module,
      _view_module_version: PanelModel.model_module_version
    };
  }

  initialize(attributes: ObjectHash, options: IBackboneModelOptions): void {
    super.initialize(attributes, options);
    this.on('comm_live_update', () => {
      if (!this.comm_live && this.comm) {
        this.close();
      }
    });
  }

  close(comm_closed?: boolean): Promise<void> {
    if (!this.get('closed')) {
      this.set('closed', true);
      if (this.comm) this.save_changes();
    }
    return super.close(comm_closed);
  }

  class_name: string; // class_name is set in widgets.py
  title: TitleModel;
  static model_name = 'PanelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'PanelView';
  static view_module = MODULE_NAME;
  static view_module_name = MODULE_VERSION;
  static serializers = {
    ...BoxModel.serializers,
    title: { deserialize: unpack_models }
  };
}

/**
 * The view for a Panel.
 */
export class PanelView extends BoxView {
  initialize(parameters: WidgetView.IInitializeParameters): void {
    super.initialize(parameters);
    this.listenTo(this.model, 'change:class_name', this.update_class_name);
    this.listenTo(this.model.get('title'), 'change', this.update_title);
    this.luminoWidget.removeClass('widget-box');
    this.luminoWidget.removeClass('jupyter-widgets');
    this.update_class_name();
    this.update_title();
  }

  update_title() {
    const title: TitleModel = this.model.get('title');
    title.update_title(this.luminoWidget.title);
  }

  update_class_name() {
    if (this.class_name) {
      this.luminoWidget.removeClass(this.class_name);
    }
    this.class_name = this.model.get('class_name');
    if (this.class_name) {
      this.luminoWidget.addClass(this.class_name);
    }
  }

  model: PanelModel;
  class_name: string = '';
  luminoWidget: JupyterLuminoPanelWidget;
}
