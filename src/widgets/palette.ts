// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ICommandPalette, IPaletteItem } from '@jupyterlab/apputils';

import { ObservableMap } from '@jupyterlab/observables';

import {
  DOMWidgetModel,
  ISerializers,
  WidgetModel,
} from '@jupyter-widgets/base';

import { IDisposable } from '@lumino/disposable';

import { MODULE_NAME, MODULE_VERSION } from '../version';

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
      _items: [],
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

    // restore existing items
    const items = this.get('_items');
    items.forEach((item: any) => this._addItem(item));
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private _onMessage(msg: any): void {
    switch (msg.func) {
      case 'addItem': {
        this._addItem(msg.payload);
        // keep track of the items
        const items = this.get('_items');
        this.set('_items', items.concat(msg.payload));
        this.save_changes();
        break;
      }
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
    const itemId = `${id}-${category}`;
    if (Private.customItems.has(itemId)) {
      // no-op if the item is already in the palette
      return;
    }
    const item = this._palette.addItem({ command: id, category, args, rank });
    Private.customItems.set(itemId, item);
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

/**
 * A namespace for private data
 */
namespace Private {
  export const customItems = new ObservableMap<IDisposable>();
}
