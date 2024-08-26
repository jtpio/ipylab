// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import {
  IDisposable,
  ISerializers,
  IpylabModel,
  JSONValue,
  onKernelLost
} from './ipylab';
import { transformObject } from './utils';

/**
 * The model for a command registry.
 */
export class CommandRegistryModel extends IpylabModel {
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

  get base() {
    return this.commands;
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

  async operation(op: string, payload: any): Promise<JSONValue | IDisposable> {
    switch (op) {
      case 'execute':
        return await this.commands.execute(payload.id, payload.args);
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
   * @param options.id
   * @param options.caption
   * @param options.label
   * @param options.iconClass
   * @param options.icon
   * @param options.commandResultTransform
   */
  private async _addCommand(options: any): Promise<IDisposable> {
    const { id, icon, commandResultTransform } = options;

    if (options.icon) {
      options.icon = (await unpack_models(icon, this.widget_manager))?.labIcon;
    }
    if (this.hasDisposable(id)) {
      this.getDisposable(id).dispose();
    }
    const command = this.commands.addCommand(id, {
      execute: async (args: any) => {
        const result = await this.scheduleOperation('execute', {
          id: id,
          kwgs: args
        });
        return await transformObject(
          result,
          commandResultTransform,
          this,
          typeof commandResultTransform === 'string'
            ? null
            : commandResultTransform
        );
      },
      isEnabled: () => this.getDisposable(id)?.config?.enabled ?? true,
      isVisible: () => this.getDisposable(id)?.config?.visible ?? true,
      isToggled: () => this.getDisposable(id)?.config?.toggled ?? true,
      ...options
    });
    (command as any).id = id;
    IpylabModel.trackDisposable(command);
    onKernelLost((this.widget_manager as any).kernel, command.dispose, command);
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

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  get model_name() {
    return 'CommandRegistryModel';
  }
}
