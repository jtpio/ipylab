// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { JupyterFrontEnd, ILabShell } from '@jupyterlab/application';

import { DOMUtils } from '@jupyterlab/apputils';

import {
  ISerializers,
  WidgetModel,
  unpack_models,
} from '@jupyter-widgets/base';

import { ArrayExt } from '@lumino/algorithm';

import { Message, MessageLoop } from '@lumino/messaging';

import { MODULE_NAME, MODULE_VERSION } from '../version';

/**
 * The model for a shell.
 */
export class ShellModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ShellModel.model_name,
      _model_module: ShellModel.model_module,
      _model_module_version: ShellModel.model_module_version,
      _widgets: [],
    };
  }

  /**
   * Initialize a ShellModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._shell = ShellModel.shell;
    this._labShell = ShellModel.labShell;

    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));

    // restore existing widgets
    const widgets = this.get('_widgets');
    widgets.forEach((w: any) => this._add(w));
  }

  /**
   * Add a widget to the application shell
   *
   * @param payload The payload to add
   */
  private async _add(payload: any): Promise<string> {
    const { serializedWidget, area, args, id } = payload;
    const model = await unpack_models(serializedWidget, this.widget_manager);
    const view = await this.widget_manager.create_view(model, {});
    const title = await unpack_models(model.get('title'), this.widget_manager);
    const luminoWidget = view.luminoWidget;

    luminoWidget.id = id ?? DOMUtils.createDomID();

    MessageLoop.installMessageHook(
      luminoWidget,
      (handler: any, msg: Message) => {
        switch (msg.type) {
          case 'close-request': {
            const widgets = this.get('_widgets').slice();
            ArrayExt.removeAllWhere(widgets, (w: any) => w.id === handler.id);
            this.set('_widgets', widgets);
            this.save_changes();
            break;
          }
        }
        return true;
      }
    );

    const updateTitle = (): void => {
      luminoWidget.title.label = title.get('label');
      luminoWidget.title.iconClass = title.get('icon_class');
      luminoWidget.title.closable = title.get('closable');
    };

    title.on('change', updateTitle);
    updateTitle();

    if ((area === 'left' || area === 'right') && this._labShell) {
      let handler;
      if (area === 'left') {
        handler = this._labShell['_leftHandler'];
      } else {
        handler = this._labShell['_rightHandler'];
      }

      // handle tab closed event
      handler.sideBar.tabCloseRequested.connect((sender: any, tab: any) => {
        tab.title.owner.close();
      });

      luminoWidget.addClass('jp-SideAreaWidget');
    }

    this._shell.add(luminoWidget, area, args);
    return luminoWidget.id;
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private async _onMessage(msg: any): Promise<void> {
    switch (msg.func) {
      case 'add': {
        const id = await this._add(msg.payload);
        // keep track of the widgets added to the shell
        const widgets = this.get('_widgets');
        this.set(
          '_widgets',
          widgets.concat({
            ...msg.payload,
            id,
          })
        );
        this.save_changes();
        break;
      }
      case 'expandLeft': {
        if (this._labShell) {
          this._labShell.expandLeft();
        }
        break;
      }
      case 'expandRight': {
        if (this._labShell) {
          this._labShell.expandRight();
        }
        break;
      }
      default:
        break;
    }
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers,
  };

  static model_name = 'ShellModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private _shell: JupyterFrontEnd.IShell;
  private _labShell: ILabShell;

  static shell: JupyterFrontEnd.IShell;
  static labShell: ILabShell;
}
