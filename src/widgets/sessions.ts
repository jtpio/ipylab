// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel
// Copyright (c) Tingkai Liu
// Distributed under the terms of the Modified BSD License.

import { SessionManager } from '@jupyterlab/services';
import { ISerializers, WidgetModel } from '@jupyter-widgets/base';
import { toArray } from '@lumino/algorithm';
import { FocusTracker } from '@lumino/widgets';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { Session } from '@jupyterlab/services';

/**
 * The model for a Session Manager
 */
export class SessionManagerModel extends WidgetModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: SessionManagerModel.model_name,
      _model_module: SessionManagerModel.model_module,
      _model_module_version: SessionManagerModel.model_module_version,
      current_session: null,
      sessions: [],
    };
  }

  /**
   * Initialize a CommandRegistryModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._sessions = SessionManagerModel.sessions;
    this._tracker = SessionManagerModel.tracker;
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
    this._sessions.runningChanged.connect(this._sendSessions, this);
    this._tracker.currentChanged.connect(this._currentChanged, this);
    this._tracker.activeChanged.connect(this._currentChanged, this);
    this._sendSessions();
    this._sendCurrent();
  }

  /**
   * Handle a custom message from the backend.
   *
   * @param msg The message to handle.
   */
  private _onMessage(msg: any): void {
    switch (msg.func) {
      case 'get_current':
        this._sendCurrent();
        break;
      default:
        break;
    }
  }


  /**
   * get sessionContext from a given widget instance
   * @param widget 
   */
  private _getSessionContext(widget: any): Session.IModel | {} {
    if (widget?.sessionContext) { // covers both ConsolePanel and NotebookPanle
      if (widget.sessionContext.session?.model){
        return widget.sessionContext.session.model;
      }
    } 
    return {}; // empty object serializes to empty dict in python
  }

  /**
   * Handle focus change in JLab
   * 
   * NOTE: currentChange fires on two situations that we are concerned about here:
   * 1. when user focuses on a widget in browser, which the `change.newValue` will 
   *  be the current Widget
   * 2. when user executes a code in console/notebook, where the `changed.newValue` will be null since
   *  we lost focus due to execution.
   * To solve this problem, we interrogate `this._tracker.currentWidget` directly.
   * We also added a simple fencing to reduce the number of Comm sync calls between Python/JS
   */
  private _currentChanged(): void {
    this._current_session = this._getSessionContext(this._tracker.currentWidget);
    this.set('current_session', this._current_session);
    this.set('sessions', toArray(this._sessions.running()));
    this.save_changes();
  }

  /**
   * Send the list of commands to the backend.
   */
  private _sendSessions(): void {
    this.set('sessions', toArray(this._sessions.running()));
    this.save_changes();
  }

  /**
   * send current session to backend
   */
  private _sendCurrent(): void {
    this._current_session = this._getSessionContext(this._tracker.currentWidget);
    this.set('current_session', this._current_session);
    this.save_changes();
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers,
  };

  static model_name = 'SessionManagerModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string = null;
  static view_module: string = null;
  static view_module_version = MODULE_VERSION;

  private _current_session: Session.IModel | {};
  private _sessions: SessionManager;
  static sessions: SessionManager;
  private _tracker: FocusTracker<any>;
  static tracker: FocusTracker<any>;
}