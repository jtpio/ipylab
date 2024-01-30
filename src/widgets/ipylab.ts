// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import {
  DOMWidgetModel,
  IBackboneModelOptions,
  ISerializers,
  WidgetModel
} from '@jupyter-widgets/base';
import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ITranslator } from '@jupyterlab/translation';
import { IWidgetRegistryData } from '@jupyter-widgets/base';
import { CommandRegistry } from '@lumino/commands';
import { JSONValue, UUID } from '@lumino/coreutils';
import { ObjectHash } from 'backbone';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { PythonBackendModel } from './python_backend';

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
    super.initialize(attributes, options);
    this._kernelId = (this.widget_manager as any).kernel.id;
    this.set('kernelId', this._kernelId);
    this._pending_backend_operation_callbacks = new Map();
    this.on('msg:custom', this._onCustomMessage.bind(this));
    const msg = `ipylab ${this.get('_model_name')} ready for operations`;
    this.send({ init: msg });
    this.on('comm_live_update', () => {
      if (!this.comm_live && this.comm) {
        this.close();
      }
    });
    this.save_changes();
  }

  get app() {
    return IpylabModel.app;
  }

  get kernelId() {
    return this._kernelId;
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
    const transform: object | string = msg.transform;

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
        var result: JSONValue = await this._fe_execute(msg.kwgs);
      } else {
        var result: JSONValue = await this.operation(operation, msg.kwgs);
      }
      var buffers = null;
      if ((result as any)?.buffers) {
        buffers = (result as any).buffers;
        delete (result as any).buffers;
      }
      if ((result as any)?.payload) result = (result as any).payload;
      const content = {
        ipylab_BE: ipylab_BE,
        operation: operation,
        payload: _transform_object(result, transform, this)
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
   * Options:
   *  - execute_method: Execute the method using dotted access.
   *
   * @param payload
   * @returns
   */
  async _fe_execute(payload: object): Promise<JSONValue> {
    const { mode, kwgs } = (payload as any).FE_execute;
    delete (payload as any).FE_execute;
    switch (mode) {
      case 'execute_method': {
        const owner = get_nested_object(
          this,
          kwgs.method.split('.').slice(0, -1).join('.')
        );
        var func = get_nested_object(this, kwgs.method) as Function;
        func = func.bind(owner, ...(payload as any).args);
        return await func();
      }
    }
  }
  /**
   *
   * @param op Name of the operation.
   * @param payload Options relevant to the operation.
   * @returns Raw result of the operation.
   */
  async operation(op: string, payload: any): Promise<JSONValue> {
    switch (op) {
      case 'myFunction':
        // do something
        return; // the result (it will get converted as required);
      default:
        // Each failed operation should throw an error if it is un-handled
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
  private _kernelId: string;
  static python_backend = new PythonBackendModel();
  static model_name: string;
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string;
  static view_module: string;
  static view_module_version = MODULE_VERSION;

  static app: JupyterFrontEnd;
  static rendermime: IRenderMimeRegistry;
  static labShell: LabShell;
  static defaultBrowser: IDefaultFileBrowser;
  static palette: ICommandPalette;
  static translator: ITranslator;
  static launcher: ILauncher;
  static exports: IWidgetRegistryData;
  static OPERATION_DONE = '--DONE--';
}

/**
 *Returns a nested object relative to `this`.
 * @param base The starting object.
 * @param path The dotted path of the object.
 * @returns
 */
export function get_nested_object(base: object, path: string): any {
  var obj: Object = base;
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
    throw new Error(
      `Failed to get the nested attribute ${path_}.${attr} ` +
        ` (base='${(base as any).name ?? 'unknown'}') `
    );
  }
  return obj;
}

/**
 * Modify the object for sending.
 * TODO: Add in 'function'
 * @param obj
 * @param options The mode as a string or an object with mode and any other parameters.
 * @param thisArg 'function' mode only - the binding of `this`.
 * @returns
 */
function _transform_object(
  obj: any,
  options: string | any,
  thisArg: object = null
): JSONValue {
  const mode = typeof options == 'string' ? options : options.mode;
  switch (mode) {
    case 'done':
      return IpylabModel.OPERATION_DONE;
    case 'raw':
      return obj as any;
    case 'null':
      return null;
    case 'string':
      return String(obj);
    case 'attribute':
      // expects simple: {parts:['dotted.attribute']}
      // or advanced: {parts:[{path:'dotted.attribute', transform:'...' }]
      const result: { [key: string]: any } = new Object();
      for (var i = 0; i < options.parts.length; i++) {
        if (typeof options.parts[i] == 'string') {
          var path = options.parts[i];
          var transform: any = 'raw';
        } else {
          var { path, transform } = options.parts[i];
        }
        var part = get_nested_object(obj, path);
        result[path] = _transform_object(part, transform);
      }
      return result;
    case 'function':
      var func = to_function(options.code).bind(thisArg);
      return func(obj);
    default:
      throw new Error(`Invalid return mode: '${options.mode}'`);
  }
}

/**
 * Convert a string definition of a function to a function object.
 * @param code The function as a string: eg. 'function (a, b) { return a + b; }'
 * @returns
 */
function to_function(code: string): Function {
  return new Function('return ' + code)();
}
