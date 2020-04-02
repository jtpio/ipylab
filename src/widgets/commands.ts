// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { ObservableMap } from '@jupyterlab/observables';

import { ISerializers, WidgetModel } from '@jupyter-widgets/base';

import { CommandRegistry } from '@lumino/commands';

import { ReadonlyPartialJSONObject } from '@lumino/coreutils';

import { IDisposable } from '@lumino/disposable';

import { MODULE_NAME, MODULE_VERSION } from '../version';

/**
 * The model for a command registry.
 */
export class CommandRegistryModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CommandRegistryModel.model_name,
      _model_module: CommandRegistryModel.model_module,
      _model_module_version: CommandRegistryModel.model_module_version,
    };
  }

  /**
   * Initialize a CommandRegistryModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._commands = CommandRegistryModel.commands;
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
    this.on('comm_live_update', () => {
      if (this.comm_live) {
        return;
      }
      this._customCommands.values().forEach((command) => command.dispose());
      this._sendCommandList();
    });
    this._sendCommandList();
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private _onMessage(msg: any): void {
    switch (msg.func) {
      case 'execute':
        this._execute(msg.payload);
        break;
      case 'addCommand':
        void this._addCommand(msg.payload);
        break;
      case 'removeCommand':
        void this._removeCommand(msg.payload);
        break;
      default:
        break;
    }
  }

  /**
   * Send the list of commands to the backend.
   */
  private _sendCommandList(): void {
    this._commands.notifyCommandChanged();
    this.set('_commands', this._commands.listCommands());
    this.save_changes();
  }

  /**
   * Execute a command
   *
   * @param bundle The command bundle.
   */
  private _execute(bundle: {
    id: string;
    args: ReadonlyPartialJSONObject;
  }): void {
    const { id, args } = bundle;
    void this._commands.execute(id, args);
  }

  /**
   * Add a new command to the command registry.
   *
   * @param options The command options.
   */
  private async _addCommand(
    options: CommandRegistry.ICommandOptions & { id: string }
  ): Promise<void> {
    const { id, caption, label, iconClass } = options;
    if (this._commands.hasCommand(id)) {
      // TODO: handle this?
      return;
    }
    const command = this._commands.addCommand(id, {
      caption,
      label,
      iconClass,
      execute: () => {
        if (!this.comm_live) {
          console.log('TODO: dispose the command');
          return;
        }
        this.send({ event: 'execute', id }, {});
      },
    });
    this._customCommands.set(id, command);
    this._sendCommandList();
  }

  /**
   * Remove a command from the command registry.
   *
   * @param bundle The command bundle.
   */
  private _removeCommand(bundle: { id: string }): void {
    const { id } = bundle;
    if (this._customCommands.has(id)) {
      this._customCommands.get(id).dispose();
    }
    this._sendCommandList();
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers,
  };

  static model_name = 'CommandRegistryModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private _commands: CommandRegistry;
  private _customCommands = new ObservableMap<IDisposable>();

  static commands: CommandRegistry;
}
