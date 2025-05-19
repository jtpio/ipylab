// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  ISerializers,
  unpack_models,
  WidgetModel
} from '@jupyter-widgets/base';
import { CommandRegistry } from '@lumino/commands';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { INotebookTracker } from '@jupyterlab/notebook';
import { ToolbarButton } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';
import { LabIcon } from '@jupyterlab/ui-components';
import { Toolbar } from '@jupyterlab/ui-components';
import { ObservableMap } from '@jupyterlab/observables';

interface IToolbarButtonOptions {
  name: string;
  execute: string;
  args: any;
  icon: string;
  iconClass: string;
  label?: string;
  tooltip?: string;
  after?: string;
  className?: string;
}

/**
 * The model for a command registry.
 */
export class CustomToolbarModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CustomToolbarModel.model_name,
      _model_module: CustomToolbarModel.model_module,
      _model_module_version: CustomToolbarModel.model_module_version
    };
  }

  /**
   * Initialize a CustomToolbarModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private async _onMessage(msg: any): Promise<void> {
    switch (msg.func) {
      case 'addToolbarButton': {
        await this.addToolbarButton(msg.payload);
        break;
      }

      case 'removeToolbarButton': {
        await this.removeToolbarButton(msg.payload['name']);
        break;
      }

      default:
        break;
    }
  }

  private async addToolbarButton(
    options: IToolbarButtonOptions
  ): Promise<void> {
    const {
      name,
      execute,
      args,
      icon,
      iconClass,
      tooltip,
      label,
      after,
      className
    } = options;

    if (Private.customToolbarButtons.has(name)) {
      console.log("button '" + name + "' already exists.");
      return;
    }

    let labIcon: LabIcon = null;
    if (icon) {
      if (icon.startsWith('IPY_MODEL_')) {
        labIcon = (await unpack_models(icon, this.widget_manager))?.labIcon;
      } else {
        labIcon = LabIcon.resolve({ icon });
      }
      if (!labIcon) {
        console.log('icon ' + icon + ' not found');
      }
    }

    const button = new ToolbarButton({
      icon: labIcon,
      iconClass: iconClass,
      onClick: () => {
        this.commands.execute(execute, args);
      },
      tooltip: tooltip,
      label: label
    });

    if (className) {
      className.split(/\s+/).forEach(button.addClass.bind(button));
    }
    if (this.toolbar.insertAfter(after, name, button as Widget)) {
      console.log("button '" + name + "' has been added.");
    }
    Private.customToolbarButtons.set(name, button);

    this._sendToolbarButtonList();
  }

  private async removeToolbarButton(name: string): Promise<void> {
    const button = Private.customToolbarButtons.get(name);
    if (button === undefined) {
      console.log("unknown button '" + name + "'.");
    } else {
      button.parent = null;
      Private.customToolbarButtons.delete(name);
    }
    this._sendToolbarButtonList();
  }

  private _sendToolbarButtonList(): void {
    this.set('_toolbar_buttons', Private.customToolbarButtons.keys());
    this.save_changes();
  }

  private get commands(): CommandRegistry {
    return CustomToolbarModel.commands;
  }

  private get toolbar(): Toolbar {
    return CustomToolbarModel.notebookTracker.currentWidget.toolbar;
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  static model_name = 'CustomToolbarModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;

  static notebookTracker: INotebookTracker;
  static commands: CommandRegistry;
}

/**
 * A namespace for private data
 */
namespace Private {
  export const customToolbarButtons = new ObservableMap<ToolbarButton>();
}
