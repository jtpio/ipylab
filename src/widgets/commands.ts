// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { CommandRegistry } from '@phosphor/commands';

import { DisposableSet } from '@phosphor/disposable';

import { ISerializers, WidgetModel } from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';

export class CommandRegistryModel extends WidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: CommandRegistryModel.model_name,
      _model_module: CommandRegistryModel.model_module,
      _model_module_version: CommandRegistryModel.model_module_version
    };
  }

  initialize(attributes: any, options: any) {
    this.commands = CommandRegistryModel._commands;
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
    this.on('comm_live_update', () => {
      if (this.comm_live) {
        return;
      }
      this._customCommands.dispose();
      this._sendCommandList();
    });
    this._sendCommandList();
  }

  private _onMessage(msg: any) {
    switch (msg.func) {
      case 'execute':
        this._execute(msg.payload);
        break;
      case 'addCommand':
        void this._addCommand(msg.payload);
        break;
      default:
        break;
    }
  }

  private _sendCommandList() {
    this.set('_commands', this.commands.listCommands());
    this.save_changes();
  }

  private _execute(payload: any) {
    const { id, args } = payload;
    void this.commands.execute(id, args);
  }

  private async _addCommand(payload: any): Promise<void> {
    const { id, caption, label, iconClass } = payload;
    if (this.commands.hasCommand(id)) {
      // TODO: handle this?
      return;
    }
    const command = this.commands.addCommand(id, {
      caption,
      label,
      iconClass,
      execute: () => {
        if (!this.comm_live) {
          console.log('TODO: dispose the command');
          return;
        }
        this.send({ event: 'execute', id }, {});
      }
    });
    this._customCommands.add(command);
    this.commands.notifyCommandChanged();
    this._sendCommandList();
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  static model_name = 'CommandRegistryModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private commands: CommandRegistry;
  static _commands: CommandRegistry;
  private _customCommands = new DisposableSet();
}
