// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  ISerializers,
  WidgetModel
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';
import { ICommandPalette } from '@jupyterlab/apputils';

export class CommandPaletteModel extends WidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: CommandPaletteModel.model_name,
      _model_module: CommandPaletteModel.model_module,
      _model_module_version: CommandPaletteModel.model_module_version
    };
  }

  initialize(attributes: any, options: any) {
    this.palette = CommandPaletteModel._palette;
    super.initialize(attributes, options);

    this.on('msg:custom', this._onMessage.bind(this));
  }

  private _onMessage(msg: any) {
    switch (msg.func) {
      case 'addItem':
        this._addItem(msg.payload);
        break;
      default:
        break;
    }
  }

  private _addItem(payload: any) {
    if (!this.palette) {
      // no-op if no palette
      return;
    }
    const { id, category, args, rank } = payload;
    void this.palette.addItem({ command: id, category, args, rank });
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers
  };

  static model_name = 'CommandPaletteModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private palette: ICommandPalette;
  static _palette: ICommandPalette;
}
