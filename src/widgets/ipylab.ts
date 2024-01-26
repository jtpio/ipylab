// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import {
  DOMWidgetModel,
  IBackboneModelOptions,
  ISerializers,
  WidgetModel
} from '@jupyter-widgets/base';

import { JSONValue } from '@lumino/coreutils';

import { ObjectHash } from 'backbone';

import { MODULE_NAME, MODULE_VERSION } from '../version';

import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';

import { CommandRegistry } from '@lumino/commands';

import { ILauncher } from '@jupyterlab/launcher';

import { ITranslator } from '@jupyterlab/translation';

import { PythonBackendModel } from './python_backend';

import { UUID } from '@lumino/coreutils';

export {
  CommandRegistry,
  IBackboneModelOptions,
  ILabShell,
  ILauncher,
  ISerializers,
  ITranslator,
  JSONValue,
  JupyterFrontEnd
};

/**
 * Base model for common features
 */
export class IpylabModel extends DOMWidgetModel {
  initialize(attributes: ObjectHash, options: IBackboneModelOptions): void {
    this._app = IpylabModel.app;
    super.initialize(attributes, options);
    this._pending_backend_operation_callbacks = new Map();
    this.on('msg:custom', this._onCustomMessage.bind(this));
    const msg = `ipylab ${this.get('_model_name')} ready for operations`;
    this.send({ init: msg });
    this.on('comm_live_update', () => {
      if (!this.comm_live && this.comm) {
        this.close();
      }
    });
  }

  get app() {
    return this._app;
  }

  check_closed() {
    if (this.get('closed')) throw Error('This object is closed');
  }

  /**
   * Convert custom messages into operations for action.
   * There are two types:
   * 1. Response to requested operation sent to Python backend.
   * 2. Operation requests received from the Python backend (ipylab_BE).
   * @param msg
   */
  private async _onCustomMessage(msg: any): Promise<void> {
    const ipylab_FE: string = msg.ipylab_FE;
    if (ipylab_FE) {
      // Frontend operation result
      delete (msg as any).ipylab_FE;
      const [resolve, reject] =
        this._pending_backend_operation_callbacks.get(ipylab_FE);
      this._pending_backend_operation_callbacks.delete(ipylab_FE);
      if (msg.error) reject(msg.error);
      else resolve(msg);
    } else {
      // Backend operation (don't await it)
      this._do_operation_for_backend(msg);
    }
  }

  /**
   * Perform an operation for the backend returning the result if successful
   * or an error 'message' if unsuccessful.
   * null results are replaced with IpylabModel.OPERATION_DONE to be replaced
   * by the backend.
   * @param msg
   */
  private async _do_operation_for_backend(msg: any) {
    const operation: string = msg.operation;
    const ipylab_BE: string = msg.ipylab_BE;

    try {
      if (!operation) {
        throw new Error(`operation not provided`);
      }

      if (!ipylab_BE) {
        throw new Error(`ipylab_BE not provided}`);
      }

      if (typeof operation != 'string')
        throw new Error(
          `operation must be a string not ${typeof operation}  operation='${operation}'`
        );

      if (operation === 'FE_execute') {
        var payload: JSONValue = await this._fe_execute(msg.kwgs);
      } else var payload: JSONValue = await this.operation(operation, msg.kwgs);

      if (payload === undefined)
        throw new Error(
          `ipylab ${this.get(
            '_model_name'
          )} bug: operation=${operation} did not return a payload!`
        );

      const buffers = (payload as any).buffers;
      delete (payload as any).buffers;
      if ((payload as any).payload) payload = (payload as any).payload;
      const content = {
        ipylab_BE: ipylab_BE,
        operation: operation,
        payload: payload
      };
      this.send(content, null, buffers);
    } catch (e) {
      const content = {
        operation: operation,
        ipylab_BE: msg.ipylab_BE,
        error: String(e)
      };
      this.send(content);
      console.error(e);
    }
  }

  /**
   * Perform execute request from backend.
   * @param payload
   * @returns
   */
  async _fe_execute(payload: object) {
    const { mode, kwgs } = (payload as any).FE_execute;
    delete (payload as any).FE_execute;

    var result: JSONValue;
    switch (mode) {
      case 'execute_method': {
        const owner = this.get_nested_object(
          kwgs.method.split('.').slice(0, -1).join('.')
        );
        var func = this.get_nested_object(kwgs.method) as Function;
        func = func.bind(owner, payload);
        result = await func();
        return result ?? IpylabModel.OPERATION_DONE;
      }
    }
  }

  /**
   *Returns a nested object relative to `this`.
   * @param path The dotted path of the object.
   * @returns
   */
  get_nested_object(path: string): object {
    var obj: Object = this;
    var path_: String = '';
    const parts = path.split('.');
    var attr = '';
    for (let i = 0; i < parts.length; i++) {
      attr = parts[i];
      if (attr in obj) {
        obj = obj[attr as keyof typeof obj];
        path_ = !path_ ? attr : `${path_}.${attr}`;
      } else break;
    }
    if (path_ != path) {
      const model = this.get('_model_name');
      path_ = path_ ? `${model}.${path_}` : model;
      throw new Error(`Invalid path: '${attr}' does not exist on '${path_}' `);
    }
    return obj;
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    // Provide any json content
    switch (op) {
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${this.get(
            '_model_name'
          )}!`
        );
    }
  }

  async schedule_operation(
    operation: string,
    payload: JSONValue
  ): Promise<JSONValue> {
    this.check_closed();
    const ipylab_FE = `${UUID.uuid4()}`;
    const msg = {
      ipylab_FE: ipylab_FE,
      operation: operation,
      payload: payload
    };
    const callbacks = this._pending_backend_operation_callbacks;
    const promise = new Promise<JSONValue>((resolve, reject) => {
      callbacks.set(ipylab_FE, [resolve, reject]);
    });
    this.send(msg);
    // TODO: await a response with corresponding ipylab_FE from the backend and return it's result or thrown an exception.
    var result = await promise;
    if (result === IpylabModel.OPERATION_DONE) result = null;
    return result;
  }

  close(comm_closed?: boolean): Promise<void> {
    if (!this.get('closed')) {
      this.set('closed', true);
      this.save_changes();
    }
    return super.close(comm_closed);
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  private _pending_backend_operation_callbacks: Map<
    string,
    [Function, Function]
  >;

  private _app!: JupyterFrontEnd;

  static python_backend = new PythonBackendModel();
  static model_name: string;
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string;
  static view_module: string;
  static view_module_version = MODULE_VERSION;

  static app: JupyterFrontEnd;
  static labShell: LabShell;
  static defaultBrowser: IDefaultFileBrowser;
  static palette: ICommandPalette;
  static translator: ITranslator;
  static launcher: ILauncher;
  static OPERATION_DONE = '--DONE--';
}
