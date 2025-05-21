// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { JupyterFrontEnd } from '@jupyterlab/application';
import { IMainMenu, MainMenu } from '@jupyterlab/mainmenu';
import { Menu } from '@lumino/widgets';

import {
  ISerializers,
  WidgetModel
  //unpack_models
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from '../version';
import { CommandRegistry } from '@lumino/commands';
import { Cell } from '@jupyterlab/cells';
import {
  INotebookTracker,
  NotebookActions,
  NotebookPanel
} from '@jupyterlab/notebook';
import { IDisposable } from '@lumino/disposable';
import { ObservableMap } from '@jupyterlab/observables';
import { ReadonlyJSONObject } from '@lumino/coreutils';

namespace CommandIDs {
  export const snippet = 'custom-menu:snippet';

  export const run_snippet = 'custom-menu:run-snippet';
}

interface IMenuOptions {
  title: string;
  spec: any;
  className?: string;
}

/**
 * The model for a shell.
 */
export class CustomMenuModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: CustomMenuModel.model_name,
      _model_module: CustomMenuModel.model_module,
      _model_module_version: CustomMenuModel.model_module_version
    };
  }

  /**
   * Initialize a ShellModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));

    this._addMenuCommand(
      CommandIDs.snippet,
      'Insert snippet in current cell',
      this._insertInActiveCell.bind(this)
    );
    this._addMenuCommand(
      CommandIDs.run_snippet,
      'Insert snippet in current cell and run it',
      this._insertInActiveCellAndRun.bind(this)
    );
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private async _onMessage(msg: any): Promise<void> {
    switch (msg.func) {
      case 'addMenu': {
        this.addMenu(msg.payload);
        break;
      }

      case 'removeMenu': {
        this.removeMenu(msg.payload);
        break;
      }

      default:
        break;
    }
  }

  /**
   *  Create a menu labeled 'title' and containing entries described by 'spec.
   */
  private createMenuFromSpec(
    title: string,
    spec: any,
    className: string
  ): Menu {
    const result = new Menu({ commands: this.commands });
    result.title.label = title;
    if (className) {
      if (result.title.className) {
        result.title.className += ' ';
      }
      result.title.className += className;
      result.addClass(className);
    }
    if (spec === null) {
      return result;
    }

    if (typeof spec[Symbol.iterator] !== 'function') {
      console.log("unknown menu type '" + spec + "'.");
      return null;
    }

    for (const entry of spec) {
      if (entry.type === 'submenu') {
        const submenu = this.createMenuFromSpec(
          entry.name,
          entry.payload,
          className
        );
        result.addItem({ type: 'submenu', submenu });
      } else if (entry.type === 'command') {
        result.addItem({ type: 'command', command: entry.payload, args: {} });
      } else if (entry.type === 'separator') {
        result.addItem({ type: 'separator' });
      } else {
        console.log("unknown menu type '" + entry.type + "'.");
      }
    }
    return result;
  }

  private hasMenu(title: string): boolean {
    return (
      this.mainMenu.menus.findIndex(
        (value, index, obj) => value.title.label === title
      ) >= 0
    );
  }

  private addMenu(options: IMenuOptions) {
    const { title, spec, className } = options;

    if (this.hasMenu(title)) {
      console.log("menu '" + title + "' already exists.");
    } else {
      const rank = this.mainMenu.helpMenu.rank - 1;
      const newMenu = this.createMenuFromSpec(title, spec, className);
      this.mainMenu.addMenu(newMenu, true, { rank });
      Private.customMenus.set(title, newMenu);
      newMenu.activate();
    }
    this._sendMenuList();
  }

  private removeMenu(options: IMenuOptions) {
    const title = options['title'];

    const menu = Private.customMenus.get(title);
    if (menu === undefined) {
      console.log("unknown menu '" + title + "'.");
    } else {
      Private.customMenus.delete(title);
      this.mainMenu.removeMenu(menu);
      this._sendMenuList();
    }
  }

  private _addMenuCommand(
    id: string,
    label: string,
    callBack: (args: ReadonlyJSONObject) => void
  ) {
    if (this.commands.hasCommand(id)) {
      Private.customCommands.get(id).dispose();
    }

    const commandEnabled = (command: IDisposable): boolean => {
      return !command.isDisposed && !!this.comm && this.comm_live;
    };

    const cmd = this.commands.addCommand(id, {
      caption: null,
      label: label,
      iconClass: null,
      icon: null,
      execute: args => {
        if (!this.comm_live) {
          cmd.dispose();
          return;
        }
        callBack(args as any);
      },
      isEnabled: () => commandEnabled(cmd),
      isVisible: () => commandEnabled(cmd)
    });
    Private.customCommands.set(id, cmd);
  }

  private _sendMenuList(): void {
    this.set('_menu_list', Private.customMenus.keys());
    this.save_changes();
  }

  private get commands(): CommandRegistry {
    return CustomMenuModel.commands;
  }

  private get mainMenu(): MainMenu {
    return CustomMenuModel.mainMenu as MainMenu;
  }

  private get notebookPanel(): NotebookPanel {
    return CustomMenuModel.notebookTracker.currentWidget;
  }

  private get activeCell(): Cell {
    return CustomMenuModel.notebookTracker.activeCell;
  }

  private async _insertInActiveCell(texts: any) {
    if (!this.activeCell) {
      await NotebookActions.insertBelow(this.notebookPanel.content);
    }
    await NotebookActions.focusActiveCell(this.notebookPanel.content, {
      waitUntilReady: true
    });

    if (this.activeCell) {
      const e = this.activeCell.editor;
      const startPos = { column: 0, line: 0 };
      const endPos = {
        column: e.getLine(e.lineCount - 1).length,
        line: e.lineCount - 1
      };
      e.focus();
      e.setSelection({ start: startPos, end: endPos });
      if (typeof texts === 'string') {
        e.replaceSelection(texts);
      } else if (typeof texts[Symbol.iterator] === 'function') {
        e.replaceSelection(texts.join('\n'));
      } else {
        e.replaceSelection(typeof texts);
      }
      await NotebookActions.changeCellType(this.notebookPanel.content, 'code');
    }
  }

  private async _insertInActiveCellAndRun(texts: any) {
    await this._insertInActiveCell(texts);
    if (this.notebookPanel) {
      const { context, content } = this.notebookPanel;
      await NotebookActions.run(content, context.sessionContext);
      await NotebookActions.selectBelow(this.notebookPanel.content);
    } else {
      console.log('no current widget');
    }
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  static model_name = 'CustomMenuModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;

  static commands: CommandRegistry;
  static notebookTracker: INotebookTracker;
  static mainMenu: IMainMenu;
  static shell: JupyterFrontEnd.IShell;
}

/**
 * A namespace for private data.
 */
namespace Private {
  export const customCommands = new ObservableMap<IDisposable>();
  export const customMenus = new ObservableMap<Menu>();
}
