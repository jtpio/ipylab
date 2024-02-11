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
import { SplitPanel, Widget } from '@lumino/widgets';
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

    const { content, kernelId, name, basePath, type, className } = options;
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
    this.addClass(className ?? 'ipylab-main-area');
    SplitPanel.setStretch(this.content, 1);
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
    this._mutex_key = `main_area ${this.model_id}`;
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
        // Using lock for mutex
        return await navigator.locks.request(this._mutex_key, () =>
          this._load_main_area_widget(payload)
        );
        this;
      case 'unload':
        return await navigator.locks.request(this._mutex_key, () =>
          this._unload_mainarea_widget()
        );
      case 'open_console':
        return await navigator.locks.request(this._mutex_key, () =>
          this._open_console(payload)
        );
      case 'close_console':
        return await navigator.locks.request(this._mutex_key, () =>
          this._close_console()
        );
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${MainAreaModel.model_name}!`
        );
    }
  }

  async _load_main_area_widget(payload: any) {
    this._unload_mainarea_widget();
    const { area, options, className } = payload;
    const content = this.get('content');
    const view = await this.widget_manager.create_view(content, {});
    const luminoWidget = new IpylabMainAreaWidget({
      content: view.luminoWidget,
      kernelId: this.kernelId,
      name: this.sessionContext.name,
      path: this.sessionContext.path,
      type: this.sessionContext.type,
      className: className
    });
    this._unload_mainarea_widget(); // unload any existing widgets.
    luminoWidget.disposed.connect(() => {
      this.set('status', 'unloaded');
      this.save_changes();
      this._luminoWidget = null;
      this._close_console();
    }, this);
    IpylabModel.app.shell.add(luminoWidget, area, options);
    await luminoWidget.sessionContext.ready;
    this._luminoWidget = luminoWidget;
    this.set('status', 'loaded');
    this.save_changes();
    return { id: this._luminoWidget.id };
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
        this.set('console_status', 'unloaded');
        this.save_changes();
      }
    }, this);
    this._consolePanel = cp;
    this.set('console_status', 'loaded');
    this.save_changes();
    return { id: cp.id };
  }

  _on_change_closed() {
    if (this.get('closed')) {
      this._unload_mainarea_widget();
    }
  }

  _close_console(): Promise<null> {
    if (this._consolePanel) {
      this._consolePanel.dispose();
    }
    return null;
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
  private _mutex_key: string;
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
     * The name of class.
     */
    className?: string;

    /**
     * The type of session.
     */
    type?: string;
  }
}
