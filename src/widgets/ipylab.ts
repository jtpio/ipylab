// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel
import {
  ISerializers,
  IWidgetRegistryData,
  WidgetModel
} from '@jupyter-widgets/base';
import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import {
  DOMUtils,
  ICommandPalette,
  Notification,
  WidgetTracker
} from '@jupyterlab/apputils';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { ObservableMap } from '@jupyterlab/observables';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel, Session } from '@jupyterlab/services';
import { ITranslator } from '@jupyterlab/translation';
import { CommandRegistry } from '@lumino/commands';

import { JSONObject, JSONValue, PromiseDelegate } from '@lumino/coreutils';
import { IDisposable } from '@lumino/disposable';
import { Signal } from '@lumino/signaling';
import { Widget } from '@lumino/widgets';
import { ObjectHash } from 'backbone';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import { IpylabPythonKernel } from './ipylab_kernel';
import {
  getNestedObject,
  listProperties,
  onKernelLost,
  setNestedAttribute,
  toFunction
} from './utils';
export {
  CommandRegistry,
  IDisposable,
  ILabShell,
  ILauncher,
  ISerializers,
  ITranslator,
  JSONObject,
  JSONValue,
  JupyterFrontEnd,
  onKernelLost,
  Widget
};
/**
 * Base model for common features
 */
export class IpylabModel extends WidgetModel {
  async initialize(attributes: ObjectHash, options: any): Promise<void> {
    super.initialize(attributes, options);
    try {
      if (this.get('cid')) {
        this._base = await this.getConnection(this.get('cid'), this.get('id'));
      } else {
        const basename = this.get('_basename');
        this._base = basename
          ? getNestedObject({
              base: this,
              path: basename,
              basename: `model_name= '${this.defaults()._model_name}`
            })
          : this;
      }
    } catch {
      this.close();
      throw new Error(`Failed to set the base so closing...`);
    }
    this.set('kernelId', this.kernelId);
    this.on('msg:custom', this._onCustomMessage, this);
    this.save_changes();
    const msg = `ipylab ${this.get('_model_name')} ready for operations`;
    this.send({ init: msg });
    onKernelLost(this.kernel, this.close, this);
  }

  get base(): any {
    return this._base;
  }

  get app() {
    return IpylabModel.app;
  }

  get rendermime() {
    return IpylabModel.rendermime;
  }

  get labShell() {
    return IpylabModel.labShell;
  }

  get defaultBrowser() {
    return IpylabModel.defaultBrowser;
  }

  get pallet() {
    return IpylabModel.palette;
  }

  get translator() {
    return IpylabModel.translator;
  }

  get launcher() {
    return IpylabModel.launcher;
  }

  get menu() {
    return IpylabModel.menu;
  }

  get commands() {
    return IpylabModel.app.commands;
  }

  get exports() {
    return IpylabModel.exports;
  }
  get kernelId() {
    return this.kernel.id;
  }
  get shell(): JupyterFrontEnd.IShell {
    return IpylabModel.app.shell;
  }

  get sessionManager(): Session.IManager {
    return IpylabModel.app.serviceManager.sessions;
  }

  get kernel(): Kernel.IKernelConnection {
    return (this.widget_manager as any).kernel;
  }

  get notificationManager() {
    return Notification.manager;
  }

  get _kernelLive() {
    const status = this.kernel?.status;
    return status ? !['dead', 'restarting'].includes(status) : false;
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
   * or an 'error' message if unsuccessful.
   * Results are 'transformed' by the method specified in the call to the operation from the backend.
   * The transformed result is returned to the backend using the ipylab_BE value (uuid4).
   * @param msg
   */
  private async _do_operation_for_backend(msg: any) {
    const operation: string = msg.operation;
    const ipylab_BE: string = msg.ipylab_BE;

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
      if (msg.toLuminoWidget instanceof Array) {
        // Replace values in kwgs with widgets
        for (const path of msg.toLuminoWidget) {
          const value = getNestedObject({
            base: msg.kwgs,
            path: path,
            nullIfMissing: false
          });
          if (value && typeof value === 'string') {
            const luminoWidget = await this.toLuminoWidget(value);
            setNestedAttribute(msg.kwgs, path, luminoWidget);
          }
        }
      }
      if (msg.toObject instanceof Array) {
        // Replace values in kwgs with attributes
        for (const path of msg.toObject) {
          const value = getNestedObject({
            base: msg.kwgs,
            path: path,
            nullIfMissing: false
          });
          if (value && typeof value === 'string') {
            const value_ = await this.toObject(value);
            setNestedAttribute(msg.kwgs, path, value_);
          }
        }
      }
      result = await this.operation(operation, msg.kwgs);
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
        payload: await this.transformObject(result, msg.transform)
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
   * Get a Lumino Widget.
   * 1. If value starts with IPY_MODEL_ it will create a new view and return the widget for that view.
   * 2. If a widget exists that has and id=value the widget will be returned.
   * 3. An errow will be thrown if the widget isn't found.
   *
   * @param value
   * @param as
   * @param string
   * @returns
   */
  async toLuminoWidget(value: string): Promise<Widget> {
    if (value.slice(0, 10) === 'IPY_MODEL_') {
      const model: any = await this.widget_manager.get_model(value.slice(10));
      if (model.get('_model_name') === IpylabModel.connection_model_name) {
        if (!(model.base instanceof Widget)) {
          throw new Error(`${value} is not a connection to a lumino widget`);
        }
        return model.base;
      }
      const view = await this.widget_manager.create_view(model, {});
      const lw = view.luminoWidget;
      onKernelLost(this.kernel, lw.dispose, lw);
      return lw;
    }
    const obj = await this.getConnection(value);
    if (!(obj instanceof Widget)) {
      throw new Error(`Not a widget '${value}'`);
    }
    return obj;
  }
  /**
   * Returns the object for the dotted path 'value'.
   * 1. If value starts with IPY_MODEL_ it will unpack the model and return
   *    the object relative to dotted path after the model name. If there is no
   *    path after the model id it will be the model.
   * 2. Otherwise the object as specified by the dotted path relate to the base will be returned.
   * 3. An error will be thrown if the value doesn't point an existing attribute.
   *
   * @param value
   * @param as
   * @param string
   * @returns
   */
  async toObject(value: string, nullIfMissing = false): Promise<any> {
    let path = value;
    let base = this as any;
    if (value.slice(0, 10) === 'IPY_MODEL_') {
      let model_id;
      [model_id, path] = value.slice(10).split('.', 2);
      base = await this.widget_manager.get_model(model_id);
      if (base.get('_model_name') === IpylabModel.connection_model_name) {
        base = base.base;
      }
    }
    return await getNestedObject({ base, path: path ?? '', nullIfMissing });
  }

  /**
   * Perform an operation and return the result. The returned result
   * will be transformed prior to returning the response message to the backend.
   *
   * @param op Name of the operation.
   * @param payload Options relevant to the operation.
   * @returns Raw result of the operation.
   */
  async operation(op: string, payload: any): Promise<JSONValue | IDisposable> {
    switch (op) {
      case 'executeCommand':
        return await this.commands.execute(payload.id, payload.args);
      case 'executeMethod':
        return await this._executeMethod(payload);
      case 'listProperties':
        return this._listProperties(payload);
      case 'setProperty':
        return this._setProperty(payload);
      case 'updateProperty':
        return this._updateProperty(payload);
      case 'getProperty':
        return await this._getProperty(payload);
      default:
        // Each failed operation should throw an error if it is un-handled
        throw new Error(
          `operation='${op}' has not been implemented in ${
            this.defaults().model_name
          }!`
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
    transform: any
  ): Promise<JSONValue> {
    const ipylab_FE = DOMUtils.createDomID();
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
    return await this.transformObject(result, transform);
  }

  private async _executeMethod(payload: any): Promise<JSONValue> {
    const { path, args } = payload;
    const obj = this.base;
    const ownername = path.split('.').slice(0, -1).join('.');
    const owner = getNestedObject({
      base: obj,
      path: ownername,
      basename: this.get('_basename')
    });
    let func = getNestedObject({ base: obj, path: path, basename: ownername });
    func = func.bind(owner, ...args);
    return await func();
  }

  private _listProperties(payload: any) {
    const { path, type, depth } = payload as any;
    return listProperties({
      obj: getNestedObject({
        base: this.base,
        path: path,
        basename: this.get('_basename')
      }),
      type: type,
      depth: depth ?? 2
    });
  }

  private _getProperty(payload: any) {
    const { path, nullIfMissing } = payload;
    return getNestedObject({
      base: this.base,
      path,
      nullIfMissing: nullIfMissing ?? false,
      basename: this.get('_basename')
    });
  }

  /**
   * Assign the values at the path instead of replacing it.
   */
  private async _updateProperty(payload: any): Promise<null> {
    const { value, valueTransform } = payload;
    const obj = this._getProperty(payload);
    const value_ = await this.transformObject(value, valueTransform);
    return Object.assign(obj, value_);
  }
  /**
   * Set an attribute at the path with transformation.
   */
  private async _setProperty(payload: any): Promise<any> {
    const { path, value, valueTransform } = payload;
    const value_ = await this.transformObject(value, valueTransform);
    setNestedAttribute(this.base, path, value_);
    return value_;
  }

  close(comm_closed?: boolean): Promise<void> {
    if (!this._base) {
      return;
    }
    this._pendingBackendOperations.forEach(opDone => opDone.reject('Closed'));
    this._pendingBackendOperations.clear();
    comm_closed = comm_closed || !this._kernelLive;
    if (!comm_closed) {
      this.send({ closed: true });
    }
    delete this._base;
    return super.close(comm_closed);
  }

  save_changes(callbacks?: {}): void {
    if (this.comm_live && this._kernelLive) {
      super.save_changes(callbacks);
    }
  }

  /**
   *
   * @param cid Get an object that has been registered as a connection.
   * @returns
   */
  async getConnection(cid: string, id: string = ''): Promise<any> {
    await IpylabModel.tracker.restored;
    if (Private.connection.has(cid)) {
      return Private.connection.get(cid);
    }
    let obj;
    if (id.slice(0, 10) === 'IPY_MODEL_') {
      obj = await this.widget_manager.get_model(id.slice(10));
      if (!(obj instanceof WidgetModel)) {
        throw new Error(`Failed to get model ${id}`);
      }
    } else {
      obj = this._getLuminoWidgetFromShell(id || cid);
    }
    IpylabModel.registerConnection(obj, cid);
    return obj;
  }

  hasConnection(cid: string) {
    return Private.connection.has(cid);
  }

  /**
   * Transform the object for sending.
   * @param obj
   * @param args The mode as a string or an object with mode and any other parameters.
   * @returns
   */
  async transformObject(obj: any, args: string | any): Promise<JSONValue> {
    const transform = typeof args === 'string' ? args : args.transform;
    let result, func;
    let cid;

    switch (transform) {
      case 'done':
        return IpylabModel.OPERATION_DONE;
      case 'raw':
        return (await obj) as any;
      case 'null':
        return null;
      case 'connection':
        cid = args?.cid ?? `ipylab-connection:${DOMUtils.createDomID()}`;
        IpylabModel.registerConnection(obj, cid);
        if (args.auto_dispose) {
          onKernelLost(this.kernel, obj.dispose, obj, true);
        }
        return { cid: cid, id: obj.id, info: args.info };
      case 'advanced':
        // expects args.mappings = {key:transform}
        result = new Object();
        for (const key of Object.keys(args.mappings)) {
          const base = getNestedObject({ base: obj, path: key });
          (result as any)[key] = await this.transformObject(
            base,
            args.mappings[key]
          );
        }
        return result as any;
      case 'function':
        func = toFunction(args.code).bind(this);
        if (func.constructor.name === 'AsyncFunction') {
          return await func(obj, args);
        }
        return func(obj);
      default:
        throw new Error(`Invalid return mode: '${transform}'`);
    }
  }

  /**
   *Keep a reference to an object so it can be found from the backend.
   * @param obj
   */
  static registerConnection(obj: any, cid: string) {
    if (typeof obj !== 'object') {
      throw new Error(`An object is required but got a '${typeof obj}'`);
    }
    if (!cid) {
      throw new Error('`cid` not provided!');
    }
    const obj_ = Private.connection.get(cid);
    if (obj_ && obj_ !== obj) {
      throw new Error(
        `Another object with cid='${cid}' is already registered!`
      );
    }
    if (!obj.dispose) {
      obj.dispose = () => '';
      obj.ipylabDisposeOnClose = true;
    }
    Private.connection.set(cid, obj);
    if (!obj.disposed) {
      // Make equivalent to an ObservableDisposable
      obj.disposed = new Signal<any, null>(obj);
      const dispose_ = obj.dispose.bind(obj);
      const dispose = () => {
        if (obj.isDisposed) {
          return;
        }
        dispose_();
        obj.disposed.emit(null);
        Signal.clearData(obj);
      };
      obj['dispose'] = dispose.bind(obj);
    }
    obj.disposed.connect(() => Private.connection.delete(cid));
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
  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: IpylabModel.model_name,
      _model_module: IpylabModel.model_module,
      _model_module_version: IpylabModel.model_module_version,
      _view_name: IpylabModel.view_name,
      _view_module: IpylabModel.view_module,
      _view_module_version: IpylabModel.view_module_version
    };
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  private _pendingBackendOperations = new Map<string, PromiseDelegate<any>>();
  private _base: object | null;
  static ipylabKernel = new IpylabPythonKernel();
  static model_name: string = 'IpylabModel';
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
  static menu: IMainMenu;
  static exports: IWidgetRegistryData;
  static OPERATION_DONE = '--DONE--';
  static connection_model_name = 'ConnectionModel';
  static tracker = new WidgetTracker<Widget>({ namespace: 'ipylab' });
}

/**
 * A namespace for private data
 */
namespace Private {
  export const connection = new ObservableMap<IDisposable>();
}
