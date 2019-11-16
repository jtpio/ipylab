// Copyright (c) Jeremy Tuloup
// Distributed under the terms of the Modified BSD License.

import { JupyterFrontEnd } from '@jupyterlab/application';

import { CommandRegistry } from '@phosphor/commands';

import {
  DOMWidgetModel, ISerializers, WidgetModel, unpack_models
} from '@jupyter-widgets/base';

import {
  VBoxModel
} from '@jupyter-widgets/controls';

import {
  MODULE_NAME, MODULE_VERSION
} from './version';

// Import the CSS
import '../css/widget.css'

export class PanelModel extends VBoxModel {

  defaults() {
    return {...super.defaults(),
      _model_name: PanelModel.model_name,
      _model_module: PanelModel.model_module,
      _model_module_version: PanelModel.model_module_version,
      _view_name: null
    };
  }

  static model_name = 'PanelModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
}

export class ShellModel extends WidgetModel {

  defaults() {
    return {...super.defaults(),
      _model_name: ShellModel.model_name,
      _model_module: ShellModel.model_module,
      _model_module_version: ShellModel.model_module_version,
    };
  }

  initialize(attributes: any, options: any) {
    this.shell = ShellModel._shell;
    super.initialize(attributes, options);
    this.on('msg:custom', this.onMessage.bind(this));
  }

  private async onMessage(msg: any) {
    switch(msg.func) {
      case 'add':
        const { serializedWidget, area, args } = msg.payload;
        const model = await unpack_models(serializedWidget, this.widget_manager);
        if (!(model instanceof PanelModel)) {
          console.error('Cannot display widget');
          return;
        }
        const view = await this.widget_manager.create_view(model, {});

        let pWidget = view.pWidget;
        pWidget.id = view.id;
        pWidget.title.closable = true;
        pWidget.disposed.connect(() => {
          view.remove();
        });
        this.shell.add(pWidget, area, args);
        break;
      default:
        break;
    }
  }

  static serializers: ISerializers = {
      ...WidgetModel.serializers,
    }

  static model_name = 'ShellModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private shell: JupyterFrontEnd.IShell;
  static _shell: JupyterFrontEnd.IShell;
}

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
