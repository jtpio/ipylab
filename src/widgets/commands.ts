// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { CommandRegistry } from '@phosphor/commands';

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

    this.set('_commands', this.commands.listCommands());
    this.save_changes();
  }

  private _onMessage(msg: any) {
    switch (msg.func) {
      case 'execute':
        this._execute(msg.payload);
        break;
      case 'addCommand':
        void this._addComnand(msg.payload);
        break;
      default:
        break;
    }
  }

  private _execute(payload: any) {
    const { id, args } = payload;
    const name = `${id}-${this.model_id}`;
    void this.commands.execute(name, args);
  }

  private async _addComnand(payload: any): Promise<void> {
    // TODO: keep track of all the user commands,
    // and dispose them all when the model is destroyed
    const { id, caption, label, iconClass } = payload;
    const name = `${id}-${this.model_id}`;
    if (this.commands.hasCommand(name)) {
      return;
    }
    void this.commands.addCommand(name, {
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
    this.commands.notifyCommandChanged();
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
}
