// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { ILabShell } from '@jupyterlab/application';

import {
  ISerializers,
  WidgetModel,
  unpack_models,
} from '@jupyter-widgets/base';

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
    super.initialize(attributes, options);
    this.on('msg:custom', this.onMessage.bind(this));
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private async onMessage(msg: any): Promise<void> {
    switch (msg.func) {
      case 'add': {
        const { serializedWidget, area, args } = msg.payload;
        const model = await unpack_models(
          serializedWidget,
          this.widget_manager
        );
        const view = await this.widget_manager.create_view(model, {});

        const title = await unpack_models(
          model.get('title'),
          this.widget_manager
        );

        const pWidget = view.pWidget;
        pWidget.id = view.id;
        pWidget.disposed.connect(() => {
          view.remove();
        });

        const updateTitle = (): void => {
          pWidget.title.label = title.get('label');
          pWidget.title.iconClass = title.get('icon_class');
          pWidget.title.closable = title.get('closable');
        };

        title.on('change', updateTitle);
        updateTitle();

        if (area === 'left' || area === 'right') {
          let handler;
          if (area === 'left') {
            handler = this._shell['_leftHandler'];
          } else {
            handler = this._shell['_rightHandler'];
          }

          // handle tab closed event
          handler.sideBar.tabCloseRequested.connect((sender: any, tab: any) => {
            tab.title.owner.close();
          });

          pWidget.addClass('jp-SideAreaWidget');
        }
        this._shell.add(pWidget, area, args);
        break;
      }
      case 'expandLeft': {
        this._shell.expandLeft();
        break;
      }
      case 'expandRight': {
        this._shell.expandRight();
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

  private _shell: ILabShell;

  static shell: ILabShell;
}
