// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  ISerializers,
  WidgetModel,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';
import { ICommandPalette, IPaletteItem } from '@jupyterlab/apputils';

/**
 * The model for a command palette.
 */
export class CommandPaletteModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CommandPaletteModel.model_name,
      _model_module: CommandPaletteModel.model_module,
      _model_module_version: CommandPaletteModel.model_module_version,
    };
  }

  /**
   * Initialize a CommandPaletteModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._palette = CommandPaletteModel.palette;
    super.initialize(attributes, options);

    this.on('msg:custom', this._onMessage.bind(this));
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private _onMessage(msg: any): void {
    switch (msg.func) {
      case 'addItem':
        this._addItem(msg.payload);
        break;
      default:
        break;
    }
  }

  /**
   * Add a new item to the command palette.
   *
   * @param options The item options.
   */
  private _addItem(options: IPaletteItem & { id: string }): void {
    if (!this._palette) {
      // no-op if no palette
      return;
    }
    const { id, category, args, rank } = options;
    void this._palette.addItem({ command: id, category, args, rank });
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
  };

  static model_name = 'CommandPaletteModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private _palette: ICommandPalette;

  static palette: ICommandPalette;
}
