// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import { ObservableMap } from '@jupyterlab/observables';
import { LabIcon } from '@jupyterlab/ui-components';
import { IDisposable } from '@lumino/disposable';
import { ISerializers, IpylabModel, JSONValue, Widget } from './ipylab';

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
    super.initialize(attributes, options);
    this.commands.commandChanged.connect(this._sendCommandList, this);
    this._sendCommandList();
  }

  get commands() {
    return IpylabModel.app.commands;
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

  async operation(op: string, payload: any): Promise<JSONValue | Widget> {
    let id, args, result, commands;
    switch (op) {
      case 'execute':
        id = payload.id;
        args = payload.args;
        return await this.commands.execute(id, args);
      case 'addPythonCommand': {
        result = await this._addCommand(payload);
        // keep track of the commands
        commands = this.get('_commands');
        this.set('_commands', commands.concat(payload));
        this.save_changes();
        return result;
      }
      case 'removePythonCommand':
        return this._removeCommand(payload.command_id);
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
    if (args && args.type !== 'added' && args.type !== 'removed') {
      return;
    }
    this.set('commands', this.commands.listCommands());
    this.save_changes();
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
  private async _addCommand(options: any): Promise<JSONValue> {
    const { id, caption, label, iconClass, icon, command_result_transform } =
      options;
    if (this.commands.hasCommand(id)) {
      const cmd = Private.customCommands.get(id);
      if (cmd) {
        cmd.dispose();
      }
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
    const command = this.commands.addCommand(id, {
      caption,
      label,
      iconClass,
      icon: labIcon,
      execute: (args: any) => {
        if (!this.comm_live) {
          command.dispose();
          return;
        }
        return this.scheduleOperation(
          'execute',
          { id: id, kwgs: args },
          command_result_transform
        );
      },
      isEnabled: () => commandEnabled(command),
      isVisible: () => commandEnabled(command)
    });
    Private.customCommands.set(id, command);
    return { id: id };
  }

  /**
   * Remove a command from the command registry.
   *
   * @param payload The command payload.
   * @param payload.id
   */
  private _removeCommand(command_id: string): null {
    if (Private.customCommands.has(command_id)) {
      const cmd = Private.customCommands.delete(command_id);
      if (cmd) {
        cmd.dispose();
      }
    }
    this.save_changes();
    return null;
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'CommandRegistryModel';
}

/**
 * A namespace for private data
 */
namespace Private {
  export const customCommands = new ObservableMap<IDisposable>();
}
