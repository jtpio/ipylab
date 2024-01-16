// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ICommandPalette, IPaletteItem } from '@jupyterlab/apputils';

import { ObservableMap } from '@jupyterlab/observables';

import { IDisposable } from '@lumino/disposable';

import { IpylabModel, JSONValue } from './ipylab';

/**
 * The model for a command palette.
 */
export class CommandPaletteModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CommandPaletteModel.model_name,
      _model_module: CommandPaletteModel.model_module,
      _model_module_version: CommandPaletteModel.model_module_version,
      _items: []
    };
  }

  /**
   * Initialize a CommandPaletteModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this._palette = CommandPaletteModel.palette;
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'addItem': {
        const id = this._addItem(payload);
        // keep track of the items
        const items = this.get('_items');
        this.set('_items', items.concat(payload));
        this.save_changes();
        return { id: id };
      }
      default:
        throw new Error(
          `event=${op} has not been implemented in CommandPaletteModel!`
        );
    }
  }

  /**
   * Add a new item to the command palette.
   *
   * @param options The item options.
   */
  private _addItem(options: IPaletteItem & { id: string }): string {
    if (!this._palette) {
      throw new Error('The command pallet is not loaded!');
    }
    const { id, category, args, rank } = options;
    const itemId = `${id}-${category}`;
    if (Private.customItems.has(itemId)) {
      // no-op if the item is already in the palette
      throw new Error(`Item with id='${itemId}' already exists`);
    }
    const item = this._palette.addItem({ command: id, category, args, rank });
    Private.customItems.set(itemId, item);
    return itemId;
  }

  static model_name = 'CommandPaletteModel';

  private _palette!: ICommandPalette;

  static palette: ICommandPalette;
}

/**
 * A namespace for private data
 */
namespace Private {
  export const customItems = new ObservableMap<IDisposable>();
}
