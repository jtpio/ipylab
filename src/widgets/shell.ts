// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { DOMUtils } from '@jupyterlab/apputils';

import { IpylabMainAreaWidget } from './main_area';

import {
  ILabShell,
  ISerializers,
  IpylabModel,
  JSONValue,
  JupyterFrontEnd
} from './ipylab';

import { unpack_models } from '@jupyter-widgets/base';

/**
 * The model for a shell.
 */
export class ShellModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: ShellModel.model_name,
      _model_module: ShellModel.model_module,
      _model_module_version: ShellModel.model_module_version
    };
  }

  /**
   * Initialize a ShellModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._shell = IpylabModel.app.shell;
    this._labShell = IpylabModel.labShell;

    super.initialize(attributes, options);
  }

  /**
   * Add a widget to the application shell
   *
   * @param payload The payload to add
   */
  private async _add(payload: any): Promise<JSONValue> {
    const { serializedWidget, area, options } = payload;
    const model = await unpack_models(serializedWidget, this.widget_manager);
    const view = await this.widget_manager.create_view(model, {});
    var luminoWidget = view.luminoWidget;
    if (area === 'main') {
      luminoWidget = new IpylabMainAreaWidget({
        content: view.luminoWidget,
        kernel_id: this.get('kernel_id'),
        name: 'Ipylab'
      });
    }
    if (!luminoWidget.id) luminoWidget.id = DOMUtils.createDomID();
    this._shell.add(luminoWidget, area, options);
    model.on('comm_live_update', () => {
      if (!model.comm_live) luminoWidget.close();
    });
    return { id: luminoWidget.id };
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'add': {
        return await this._add(payload);
      }
      case 'expandLeft': {
        if (this._labShell) {
          this._labShell.expandLeft();
        }
        return IpylabModel.OPERATION_DONE;
      }
      case 'expandRight': {
        this._labShell.expandRight();
        return IpylabModel.OPERATION_DONE;
      }
      case 'collapseLeft': {
        this._labShell.collapseLeft();
        return IpylabModel.OPERATION_DONE;
      }
      case 'collapseRight': {
        if (this._labShell) {
          this._labShell.collapseRight();
        }
      }
      case 'collapseRight': {
        this._labShell.collapseRight();
        return IpylabModel.OPERATION_DONE;
      }
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${this.get(
            '_model_name'
          )}!`
        );
    }
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'ShellModel';

  private _shell: JupyterFrontEnd.IShell;
  private _labShell: ILabShell;
}
