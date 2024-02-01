// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { IBackboneModelOptions, unpack_models } from '@jupyter-widgets/base';
import {
  ISessionContext,
  MainAreaWidget,
  SessionContext
} from '@jupyterlab/apputils';
import { ConsolePanel } from '@jupyterlab/console';
import { PathExt } from '@jupyterlab/coreutils';
import { UUID } from '@lumino/coreutils';
import { Message } from '@lumino/messaging';
import { Widget } from '@lumino/widgets';
import { ObjectHash } from 'backbone';
import { IpylabModel, JSONValue } from './ipylab';
/**
 * A main area widget with a sessionContext and the ability to add other children.
 */
export class IpylabMainAreaWidget extends MainAreaWidget {
  /**
   * Construct a MainAreaWidget with a context.
   * closing in the shell
   */
  constructor(options: IpylabMainAreaWidget.IOptions) {
    //TODO: support more parts of the MainAreaWidget

    const { content, kernelId, name, basePath, type } = options;
    let path = options.path;
    super({ content: content });
    if (!path) {
      path = PathExt.join(basePath || '', `${name}-${UUID.uuid4()}`);
    }
    this._sessionContext = new SessionContext({
      sessionManager: IpylabModel.app.serviceManager.sessions,
      specsManager: IpylabModel.app.serviceManager.kernelspecs,
      path: path,
      name: name,
      type: type || 'ipylab',
      kernelPreference: {
        id: kernelId,
        language: 'python3'
      }
    });
    this._sessionContext.initialize();
    this.node.removeChild(this.toolbar.node); // Temp until toolbar is supported
  }

  /**
   * The session used by the main area.
   */
  get sessionContext(): ISessionContext {
    return this._sessionContext;
  }

  /**
   * Dispose the widget.
   *
   */
  dispose(): void {
    if (this.isDisposed) {
      return;
    }
    this.sessionContext.dispose();
    super.dispose();
  }

  /**
   * Handle `'close-request'` messages.
   */
  protected onCloseRequest(msg: Message): void {
    super.onCloseRequest(msg);
    this.dispose();
  }

  private _sessionContext: ISessionContext;
}

/**
 * The model for controlling the content of a MainArea.
 * This model can:
 * - add/remove itself from the shell.
 * - open/close a console with a maximum of one console open.
 *
 */
export class MainAreaModel extends IpylabModel {
  async initialize(
    attributes: ObjectHash,
    options: IBackboneModelOptions
  ): Promise<void> {
    super.initialize(attributes, options);
    this._sessionContext = new SessionContext({
      sessionManager: IpylabModel.app.serviceManager.sessions,
      specsManager: IpylabModel.app.serviceManager.kernelspecs,
      path: this.get('path'),
      name: this.get('name'),
      type: 'ipylab main area',
      kernelPreference: { id: this.kernelId, language: 'python3' }
    });
    await this.sessionContext.initialize();
    this.on('change:closed', this._on_change_closed, this);
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'load':
        await this._load_main_area_widget(payload);
        return IpylabModel.OPERATION_DONE;
      case 'unload':
        this._unload_mainarea_widget();
        return IpylabModel.OPERATION_DONE;
      case 'open_console':
        return await this._open_console(payload);
      case 'close_console':
        this._close_console();
        return IpylabModel.OPERATION_DONE;
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${MainAreaModel.model_name}!`
        );
    }
  }

  async _load_main_area_widget(payload: any) {
    const { area, options, className } = payload;
    const content = this.get('content');
    const view = await this.widget_manager.create_view(content, {});
    const luminoWidget = new IpylabMainAreaWidget({
      content: view.luminoWidget,
      kernelId: this.kernelId,
      name: this.sessionContext.name,
      path: this.sessionContext.path,
      type: this.sessionContext.type
    });
    luminoWidget.revealed;
    if (className) {
      luminoWidget.addClass(className);
    }
    luminoWidget.disposed.connect(() => {
      this.set('loaded', false);
      this.save_changes();
      this._luminoWidget = null;
      this._close_console();
    }, this);
    this._unload_mainarea_widget();
    IpylabModel.app.shell.add(luminoWidget, area, options);
    await luminoWidget.sessionContext.ready;
    this._luminoWidget = luminoWidget;
    this.set('loaded', true);
    this.save_changes();
  }

  _unload_mainarea_widget() {
    if (this._luminoWidget) {
      this._luminoWidget.dispose();
    }
    this._close_console();
  }
  async _open_console(options: any) {
    // https://jupyterlab.readthedocs.io/en/stable/api/interfaces/console.ConsolePanel.IOptions.html
    this._close_console();
    const cp: ConsolePanel = await IpylabModel.app.commands.execute(
      'console:create',
      {
        basePath: this.sessionContext.path,
        // type: 'Linked Console',
        ref: this._luminoWidget?.id,
        kernelPreference: { id: this.kernelId, language: 'python3' },
        ...options
      }
    );
    // The console toobar takes up space and currently only provides a debugger
    if (cp?.toolbar?.node) {
      cp.node.removeChild(cp.toolbar.node);
    }
    await cp.sessionContext.ready;
    cp.disposed.connect(() => {
      if (this._consolePanel === cp) {
        this._consolePanel = null;
        this.set('console_loaded', false);
        this.save_changes();
      }
    }, this);
    this._consolePanel = cp;
    this.set('console_loaded', true);
    this.save_changes();
    return { id: cp.id };
  }

  _on_change_closed() {
    if (this.get('closed')) {
      this._unload_mainarea_widget();
    }
  }

  _close_console() {
    if (this._consolePanel) {
      this._consolePanel.dispose();
    }
  }

  /**
   * The session used by the main area.
   */
  get sessionContext(): ISessionContext {
    return this._sessionContext;
  }

  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: MainAreaModel.model_name,
      _model_module: IpylabModel.model_module,
      _model_module_version: IpylabModel.model_module_version,
      _view_name: MainAreaModel.view_name,
      _view_module: IpylabModel.model_module,
      _view_module_version: IpylabModel.model_module_version
    };
  }
  private _luminoWidget: IpylabMainAreaWidget;
  private _consolePanel: ConsolePanel;
  private _sessionContext: ISessionContext;

  static model_name = 'MainAreaModel';
  static view_name = 'MainAreaView';
  class_name = 'ipylab-main_area';
  static serializers = {
    ...IpylabModel.serializers,
    content: { deserialize: unpack_models }
  };
}

/**
 * A namespace for IpylabMainAreaWidget statics.
 */
export namespace IpylabMainAreaWidget {
  /**
   * The initialization options for a main area panel.
   */
  export interface IOptions {
    /**
     * The widget to use in the main area.
     */
    content: Widget;

    /**
     * The id of the python kernel.
     */
    kernelId: string;

    /**
     * The path of an existing session.
     */
    path?: string;

    /**
     * The base path for a new sessions.
     */
    basePath?: string;

    /**
     * The name of the IpylabMainAreaWidget.
     */
    name: string;

    /**
     * The type of session.
     */
    type?: string;
  }
}
