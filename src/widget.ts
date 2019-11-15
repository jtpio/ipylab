// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { JupyterFrontEnd } from '@jupyterlab/application';

import { CommandRegistry } from '@phosphor/commands';

import {
  DOMWidgetModel, ISerializers, WidgetModel
} from '@jupyter-widgets/base';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';

// Import the CSS
import '../css/widget.css'

export class CommandRegistryModel extends WidgetModel {

  defaults() {
    return {...super.defaults(),
      _model_name: CommandRegistryModel.model_name,
      _model_module: CommandRegistryModel.model_module,
      _model_module_version: CommandRegistryModel.model_module_version,
    };
  }

  initialize(attributes: any, options: any) {
    this.commands = CommandRegistryModel._commands;
    super.initialize(attributes, options);
    this.on('msg:custom', this.onMessage.bind(this));
  }

  private onMessage(msg: any) {
    switch(msg.func) {
      case 'execute':
        const { command, args } = msg.payload;
        this.commands.execute(command, args);
        break;
      default:
        break;
    }
  }

  static serializers: ISerializers = {
      ...WidgetModel.serializers,
    }

  static model_name = 'CommandRegistryModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private commands: CommandRegistry;
  static _commands: CommandRegistry;
}

export class JupyterFrontEndModel extends WidgetModel {

  defaults() {
    return {...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name,
      _model_module: JupyterFrontEndModel.model_module,
      _model_module_version: JupyterFrontEndModel.model_module_version,
    };
  }

  initialize(attributes: any, options: any) {
    this.app = JupyterFrontEndModel._app;
    console.log(this.app);
    super.initialize(attributes, options);
  }

  static serializers: ISerializers = {
      ...DOMWidgetModel.serializers,
    }

  static model_name = 'JupyterFrontEndModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private app: JupyterFrontEnd;
  static _app: JupyterFrontEnd;
}
