// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ObservableMap } from '@jupyterlab/observables';

import {
  CommandRegistry,
  ISerializers,
  IpylabModel,
  JSONValue
} from './ipylab';

import { IDisposable } from '@lumino/disposable';

import { LabIcon } from '@jupyterlab/ui-components';

import { unpack_models } from '@jupyter-widgets/base';

/**
 * The model for a command registry.
 */
export class CommandRegistryModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CommandRegistryModel.model_name,
      _model_module: CommandRegistryModel.model_module,
      _model_module_version: CommandRegistryModel.model_module_version,
      _command_list: [],
      _commands: []
    };
  }

  /**
   * Initialize a CommandRegistryModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._commands = IpylabModel.app.commands;
    super.initialize(attributes, options);
    this.on('comm_live_update', () => {
      if (this.comm_live) {
        return;
      }
      Private.customCommands.values().forEach(command => command.dispose());
    });

    this._commands.commandChanged.connect(this._sendCommandList, this);
    this._sendCommandList();
  }

  /**
   * Close model
   *
   * @param comm_closed - true if the comm is already being closed. If false, the comm will be closed.
   *
   * @returns - a promise that is fulfilled when all the associated views have been removed.
   */
  close(comm_closed = false): Promise<void> {
    // can only be closed once.
    this._commands.commandChanged.disconnect(this._sendCommandList, this);
    return super.close(comm_closed);
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'execute':
        return await this._execute(payload);
      case 'addCommand': {
        await this._addCommand(payload);
        // keep track of the commands
        const commands = this.get('_commands');
        this.set('_commands', commands.concat(payload));
        this.save_changes();
        return IpylabModel.OPERATION_DONE;
      }
      case 'removeCommand':
        this._removeCommand(payload.command_id);
        return IpylabModel.OPERATION_DONE;
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${this.get(
            '_model_name'
          )}!`
        );
    }
  }

  /**
   * Send the list of commands to the backend.
   */
  private _sendCommandList(sender?: object, args?: any): void {
    // this._commands.notifyCommandChanged();
    if (args && args.type != 'added' && args.type != 'removed') return;
    this.set('commands', this._commands.listCommands());
    this.save_changes();
  }

  /**
   * Execute a command
   *
   * @param payload The command payload.
   * @param payload.id
   * @param payload.args
   */
  private async _execute(payload: any): Promise<JSONValue> {
    const { id, args } = payload;
    const result = await this._commands.execute(id, args);
    try {
      if (result.toJSON) return result.toJSON();
      if (result.id) return { id: result.id };
      return result;
    } catch (e) {
      return IpylabModel.OPERATION_DONE;
    }
  }

  /**
   * Add a new command to the command registry.
   *
   * @param payload The command options.
   * @param options.id
   * @param options.caption
   * @param options.label
   * @param options.iconClass
   * @param options.icon
   */
  private async _addCommand(options: any): Promise<void> {
    const { id, caption, label, iconClass, icon } = options;
    if (this._commands.hasCommand(id)) {
      const cmd = Private.customCommands.get(id);
      if (cmd) cmd.dispose();
    }

    let labIcon: LabIcon | null = null;
    if (icon) {
      labIcon = (await unpack_models(icon, this.widget_manager))?.labIcon;
    }

    // TODO: Add better support for enabling/disabling commands
    // Add synchronized lists for disabled and hidden
    const commandEnabled = (command: IDisposable): boolean => {
      return !command.isDisposed && !!this.comm && this.comm_live;
    };
    const command = this._commands.addCommand(id, {
      caption,
      label,
      iconClass,
      icon: labIcon,
      execute: (args: any) => {
        if (!this.comm_live) {
          command.dispose();
          return;
        }
        return this.schedule_operation('execute', { id: id, kwgs: args });
      },
      isEnabled: () => commandEnabled(command),
      isVisible: () => commandEnabled(command)
    });
    Private.customCommands.set(id, command);
  }

  /**
   * Remove a command from the command registry.
   *
   * @param payload The command payload.
   * @param payload.id
   */
  private _removeCommand(command_id: string): void {
    if (Private.customCommands.has(command_id)) {
      const cmd = Private.customCommands.get(command_id);
      if (cmd) cmd.dispose();
    }
    this.save_changes();
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'CommandRegistryModel';

  private _commands!: CommandRegistry;
}

/**
 * A namespace for private data
 */
namespace Private {
  export const customCommands = new ObservableMap<IDisposable>();
}
