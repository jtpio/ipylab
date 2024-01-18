// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import { MODULE_NAME, MODULE_VERSION } from '../version';

import { Session } from '@jupyterlab/services';

import { ILabShell, JupyterFrontEnd } from '@jupyterlab/application';

import { ISerializers, IpylabModel, JSONValue } from './ipylab';

/**
 * The model for a Session Manager
 */
export class SessionManagerModel extends IpylabModel {
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
      sessions: []
    };
  }

  /**
   * Initialize a SessionManagerModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    const { labShell, sessions, shell } = SessionManagerModel;
    this._sessions = sessions;
    this._shell = shell;
    this._labShell = labShell;

    sessions.runningChanged.connect(this._sendSessions, this);

    super.initialize(attributes, options);

    if (this._labShell) {
      this._labShell.currentChanged.connect(this._currentChanged, this);
      this._labShell.activeChanged.connect(this._currentChanged, this);
    } else {
      this._currentChanged();
    }

    this._sendSessions();
    this._sendCurrent();
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'refreshRunning':
        await this._sessions.refreshRunning();
        this._currentChanged();
        return this.get('sessions');
      default:
        throw new Error(
          `event=${op} has not been implemented ${SessionManagerModel.model_name}!`
        );
    }
  }

  /**
   * get sessionContext from a given widget instance
   *
   * @param widget widget tracked by app.shell._track (FocusTracker)
   */
  private _getSessionContext(
    widget: any
  ): Session.IModel | Record<string, unknown> {
    return widget?.sessionContext?.session?.model ?? {};
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
    this._current_session = this._getSessionContext(this._shell.currentWidget);
    this.set('current_session', this._current_session);
    this.set('sessions', Array.from(this._sessions.running()));
    this.save_changes();
  }

  /**
   * Send the list of sessions to the backend.
   */
  private _sendSessions(): void {
    this.set('sessions', Array.from(this._sessions.running()));
    this.save_changes();
  }

  /**
   * send current session to backend after init
   */
  private _sendCurrent(): void {
    this._current_session = this._getSessionContext(this._shell.currentWidget);
    this.set('current_session', this._current_session);
    this.set('app_session', this._current_session);
    this.save_changes();
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'SessionManagerModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string;
  static view_module: string;
  static view_module_version = MODULE_VERSION;

  private _current_session!: Session.IModel | Record<string, unknown>;
  private _sessions!: Session.IManager;
  static sessions: Session.IManager;
  private _shell!: JupyterFrontEnd.IShell;
  private _labShell!: ILabShell;
  static shell: JupyterFrontEnd.IShell;
  static labShell: ILabShell;
}
