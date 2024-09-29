// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { CommandRegistry } from '@lumino/commands';
import { IDisposable, IpylabModel } from './ipylab';
/**
 * The model for a command registry.
 */
export class CommandRegistryModel extends IpylabModel {
  async ipylabInit(base: any = null) {
    this.commands.commandChanged.connect(this._sendCommandList, this);
    this._sendCommandList();
    await super.ipylabInit(base);
  }

  /**
   * Close model
   *
   * @param comm_closed - true if the comm is already being closed. If false, the comm will be closed.
   *
   * @returns - a promise that is fulfilled when all the associated views have been removed.
   */
  close(comm_closed = false): Promise<void> {
    this.commands.commandChanged.disconnect(this._sendCommandList, this);
    return super.close(comm_closed);
  }

  async operation(op: string, payload: any): Promise<any> {
    switch (op) {
      case 'addCommand': {
        return await this._addCommand(payload);
      }
      default:
        return await super.operation(op, payload);
    }
  }

  /**
   * Send the list of commands to the backend.
   */
  private _sendCommandList(sender?: object, args?: any): void {
    if (args && args.type !== 'added' && args.type !== 'removed') {
      return;
    }
    this.set('all_commands', this.commands.listCommands());
    this.save_changes();
  }

  /**
   * Add a new command to the command registry.
   *
   * @param payload The command options.
   */
  private async _addCommand(
    options: CommandRegistry.ICommandOptions & { id: string }
  ): Promise<IDisposable> {
    const { id, isToggleable, icon } = options;

    if (IpylabModel.connections.has(id)) {
      (await IpylabModel.fromConnectionOrId(id)).dispose();
    }
    // Make a new object and define functions so we can dynamically update.
    const config = { ...options };
    delete config.icon;
    const isToggled = isToggleable ? () => config.isToggled ?? true : null;
    const options_ = {
      caption: () => config.caption ?? '',
      className: () => config.className ?? '',
      dataset: () => config.dataset ?? {},
      describedBy: () => config.describedBy ?? '',
      execute: async (args: any) => {
        return await this.scheduleOperation('execute', { id, args }, 'object');
      },
      icon: icon,
      iconClass: () => config.iconClass ?? '',
      iconLabel: () => config.iconLabel ?? '',
      isEnabled: () => config.isEnabled ?? true,
      isToggleable,
      isToggled,
      isVisible: () => config.isVisible ?? true,
      label: () => config.label,
      mnemonic: () => Number(config.mnemonic ?? -1),
      usage: () => config.usage ?? ''
    };
    const command = this.commands.addCommand(id, options_ as any);
    (command as any).id = id;
    (command as any).config = config;
    return command;
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: CommandRegistryModel.model_name
    };
  }
  static model_name = 'CommandRegistryModel';
}
