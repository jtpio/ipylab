// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import { SessionManager, Session } from '@jupyterlab/services';
import { ISerializers, WidgetModel } from '@jupyter-widgets/base';
import { toArray } from '@lumino/algorithm';
import { MODULE_NAME, MODULE_VERSION } from '../version';

/**
 * The model for a command registry.
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
    super.initialize(attributes, options);
    this.on('msg:custom', this._onMessage.bind(this));
    this._sessions.runningChanged.connect(this._sendSessions, this);
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
   * Send the list of commands to the backend.
   */
  private _sendSessions(): void {
    this.set('sessions', toArray(this._sessions.running()));
    this.save_changes();
  }

  /**
   * get current session to the backend.
   * TODO: need to implement
   */
  private _getCurrent(): void {
    this._current_session = undefined;
  }

  /**
   * send current session to backend
   */
  private _sendCurrent(): void {
    if (!this._current_session) {
      this._getCurrent();
    }
    this.set('current_sessions', this._current_session);
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

  private _current_session: Session.IModel;

  private _sessions: SessionManager;
  static sessions: SessionManager;
}