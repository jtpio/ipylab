// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import {
  DOMWidgetModel,
  IBackboneModelOptions,
  ISerializers,
  IWidgetRegistryData,
  WidgetModel,
  unpack_models
} from '@jupyter-widgets/base';
import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { ITranslator } from '@jupyterlab/translation';
import { CommandRegistry } from '@lumino/commands';
import { JSONObject, JSONValue, UUID } from '@lumino/coreutils';
import { ObjectHash } from 'backbone';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { PythonBackendModel } from './python_backend';
import { PromiseDelegate } from '@lumino/coreutils';
import {
  getNestedObject,
  listAttributes,
  onKernelLost,
  transformObject
} from './utils';

export {
  CommandRegistry,
  IBackboneModelOptions,
  ILabShell,
  ILauncher,
  ISerializers,
  ITranslator,
  JSONObject,
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
    this.on('msg:custom', this._onCustomMessage.bind(this));
    this.save_changes();
    const msg = `ipylab ${this.get('_model_name')} ready for operations`;
    this.send({ init: msg });
    onKernelLost((this.widget_manager as any).kernel, this.close, this);
  }

  get app() {
    return IpylabModel.app;
  }

  get kernelId() {
    return this._kernelId;
  }

  get kernelLive() {
    const status = (this.widget_manager as any)?.kernel?.status;
    return status ? !['dead'].includes(status) : false;
  }

  /**
   * Convert custom messages into operations for action.
   * There are two types:
   * 1. Response to requested operation sent to Python backend (ipylab_FE).
   * 2. Operation requests received from the Python backend (ipylab_BE).
   * @param msg
   */
  private _onCustomMessage(msg: any) {
    if (msg.ipylab_FE) {
      // Frontend operation result
      const opDone = this._pendingBackendOperations.get(msg.ipylab_FE);
      this._pendingBackendOperations.delete(msg.ipylab_FE);
      if (opDone) {
        if (msg.error) {
          opDone.reject(new Error(msg.error?.repr ?? msg.error));
        } else {
          opDone.resolve(msg.payload);
        }
      }
    } else if (msg.ipylab_BE) {
      this._do_operation_for_backend(msg);
    }
  }

  /**
   * Perform an operation for the backend returning the result if successful
   * or an error 'message' if unsuccessful.
   * Results are 'transformed' by the method specified in the call to the operation from the backend.
   * The transformed result is returned to the backend using the ipylab_BE value (uuid4).
   * @param msg
   */
  private async _do_operation_for_backend(msg: any) {
    const operation: string = msg.operation;
    const ipylab_BE: string = msg.ipylab_BE;
    const transform: object | string = msg.transform;

    try {
      if (!operation) {
        throw new Error('operation not provided');
      }

      if (!ipylab_BE) {
        throw new Error('ipylab_BE not provided}');
      }

      if (typeof operation !== 'string') {
        throw new Error(
          `operation must be a string not ${typeof operation}  operation='${operation}'`
        );
      }
      let result;
      if (operation === 'FE_execute') {
        result = await this._fe_execute(msg.kwgs);
      } else {
        result = await this.operation(operation, msg.kwgs);
      }
      let buffers = null;
      if ((result as any)?.buffers) {
        buffers = (result as any).buffers;
        delete (result as any).buffers;
      }
      if ((result as any)?.payload) {
        result = (result as any).payload;
      }
      const content = {
        ipylab_BE: ipylab_BE,
        operation: operation,
        payload: await transformObject(result, transform, this)
      };
      this.send(content, null, buffers);
    } catch (e) {
      const content = {
        operation: operation,
        ipylab_BE: msg.ipylab_BE,
        error: `${(e as Error).message}`
      };
      this.send(content);
      console.error(e);
    }
  }

  /**
   * Perform execute request from backend.
   * Options:
   *  - executeMethod: Execute the method using dotted access.
   *      eg. 'shell.expandLeft' will execute the method this.shell.expandLeft
   *      args must be passed in an array in the as defined in the method.
   * @param payload
   * @returns
   */
  async _fe_execute(payload: object): Promise<JSONValue> {
    const { mode, kwgs } = (payload as any).FE_execute;
    delete (payload as any).FE_execute;
    switch (mode) {
      case 'executeMethod': {
        let obj;
        (obj as any) = this;
        if (kwgs.widget) {
          if (typeof kwgs.widget === 'string') {
            obj = this._getLuminoWidgetFromShell(kwgs.widget);
          } else {
            obj = await unpack_models(kwgs.widget, this.widget_manager);
          }
        }
        const owner = getNestedObject(
          obj,
          kwgs.method.split('.').slice(0, -1).join('.')
        );
        let func = getNestedObject(obj, kwgs.method);
        func = func.bind(owner, ...(payload as any).args);
        return await func();
      }
    }
  }
  /**
   * Perform an operation and return the result. The returned result
   * will be transformed prior to returning the response message to the backend.
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

  /**
   * Schedule an operation to be performed on the backend.
   * This is a mirror of 'schedule_operation' on the backend.
   *
   * @param operation The name of the operation to perform on the backend.
   * @param payload Corresponding payload as expected by the backend.
   * @returns
   */
  async scheduleOperation(
    operation: string,
    payload: JSONValue,
    transform?: object | string
  ): Promise<JSONValue> {
    const ipylab_FE = `${UUID.uuid4()}`;
    const msg = {
      ipylab_FE: ipylab_FE,
      operation: operation,
      payload: payload
    };
    // Create callbacks to be resolved when a custom message is received
    // with the key `ipylab_FE`.
    const opDone = new PromiseDelegate();
    this._pendingBackendOperations.set(ipylab_FE, opDone);
    this.send(msg);
    const result: any = await opDone.promise;
    return await transformObject(result, transform ?? 'raw', this);
  }

  listAttributes(path: string, type = '', depth = 2) {
    return listAttributes({
      obj: getNestedObject(this, path),
      type: type,
      depth: depth
    });
  }

  getAttribute(path: string) {
    return getNestedObject(this, path);
  }

  close(comm_closed?: boolean): Promise<void> {
    this._pendingBackendOperations.forEach(opDone => opDone.reject('Closed'));
    this._pendingBackendOperations.clear();
    comm_closed = comm_closed || !this.kernelLive;
    return super.close(comm_closed);
  }

  save_changes(callbacks?: unknown): void {
    if (this.comm_live && this.kernelLive) {
      super.save_changes(callbacks);
    }
  }

  /**
   * Get the lumino widget from the shell using its id.
   *
   * @param id
   * @returns
   */
  _getLuminoWidgetFromShell(id: string) {
    for (const area of [
      'main',
      'header',
      'top',
      'menu',
      'left',
      'right',
      'bottom',
      'down'
    ]) {
      for (const widget of IpylabModel.labShell.widgets(
        area as ILabShell.Area
      )) {
        if (widget.id === id) {
          return widget;
        }
      }
      throw new Error(`Lumino widget with id='${id}' not found in the shell.`);
    }
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  private _pendingBackendOperations = new Map<string, PromiseDelegate<any>>();
  private _kernelId: string;
  static pythonBackend = new PythonBackendModel();
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
