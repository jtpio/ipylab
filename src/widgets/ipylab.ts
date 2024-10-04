// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  ICallbacks,
  ISerializers,
  IWidgetRegistryData,
  WidgetModel
} from '@jupyter-widgets/base';
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import {
  ICommandPalette,
  Notification,
  SessionContext,
  SessionContextDialogs,
  WidgetTracker
} from '@jupyterlab/apputils';
import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';
import { ILauncher } from '@jupyterlab/launcher';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { ObservableMap } from '@jupyterlab/observables';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import type { Kernel, Session } from '@jupyterlab/services';
import { ITranslator } from '@jupyterlab/translation';
import { CommandRegistry } from '@lumino/commands';
import {
  JSONObject,
  JSONValue,
  PromiseDelegate,
  UUID
} from '@lumino/coreutils';
import { IDisposable, IObservableDisposable } from '@lumino/disposable';
import { Signal } from '@lumino/signaling';
import { Widget } from '@lumino/widgets';
import { MODULE_NAME, MODULE_VERSION } from '../version';
import type { JupyterFrontEndModel } from './frontend';
import {
  getNestedObject,
  listProperties,
  setNestedProperty,
  toFunction
} from './utils';
export {
  CommandRegistry,
  IDisposable,
  ILabShell,
  ILauncher,
  IObservableDisposable,
  ISerializers,
  ITranslator,
  JSONObject,
  JSONValue,
  JupyterFrontEnd,
  Widget
};

/**
 * Base model for common features
 */
export class IpylabModel extends WidgetModel {
  initialize(attributes: Backbone.ObjectHash, options: any): void {
    super.initialize(attributes, options);
    this.set('kernelId', this.kernelId);
    this.send({ init: 'ipylabInit' });
    this.ipylabInit();
  }

  /**
   * Finish initializing the model.
   * Overload this method as required.
   *
   * When overloading nsuring to call:
   *  `await super.ipylabInit()`
   *
   * @param base The base of the model with regard to all methods that use base.
   */
  async ipylabInit(base: any = null) {
    if (!base) {
      const dottedname = this.get('_basename');
      base = this;
      if (dottedname) {
        try {
          base = getNestedObject({ base, dottedname });
        } catch {
          this.close();
          throw new Error(
            `Failed locate _basename = '${dottedname}' so closing...`
          );
        }
      }
    }
    this._base = base;
    this.on('msg:custom', this._onCustomMessage, this);
    IpylabModel.onKernelLost(this.kernel, this.close, this);
    this.save_changes();
    this.send({ init: 'ready' });
  }

  get model_name() {
    return this.get('_model_name');
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

  close(comm_closed?: boolean): Promise<void> {
    if (!this._base) {
      return;
    }
    this._pendingOperations.forEach(opDone => opDone.reject('Closed'));
    this._pendingOperations.clear();
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
   * Send a custom msg over the comm.
   */
  send(
    content: any,
    callbacks?: ICallbacks,
    buffers?: ArrayBuffer[] | ArrayBufferView[]
  ) {
    let content_: string;
    try {
      content_ = JSON.stringify(content);
    } catch {
      // Assuming the error is due to circular reference
      content_ = JSON.stringify(content, IpylabModel._replacer);
    }
    super.send(content_, callbacks, buffers);
  }

  static _replacer(key: string, value: any) {
    // Filtering out properties
    if (key === 'payload') {
      const out = listProperties({
        obj: value,
        omitHidden: true,
        depth: 3
      });
      out['WARNING'] =
        'This payload is a simplified representation because it has circular references.';
      if (typeof value.dispose === 'function') {
        // Keep a reference to disposable objects in case it needs to be found again in the frontend.
        // Not intended to be used by the backend as a connection transform is available.
        const cid = (out['ipylab_cid'] = `ipylab-connection:${UUID.uuid4()}`);
        IpylabModel.registerConnection(cid, value);
      }
      return out;
    }
    return value;
  }

  /**
   * Convert custom messages into operations for action.
   * There are two types:
   * 1. Response to requested operation sent to Python backend (ipylab_FE).
   * 2. Operation requests received from the Python backend (ipylab_BE).
   * @param msg
   */
  private async _onCustomMessage(msg: any) {
    if (typeof msg !== 'string') {
      return;
    }
    const content = JSON.parse(msg);
    if (content.toLuminoWidget instanceof Array) {
      // Replace values in kwgs with widgets
      for (const dottedname of content.toLuminoWidget) {
        const value = getNestedObject({
          base: content.kwgs,
          dottedname,
          nullIfMissing: false
        });
        if (value && typeof value === 'string') {
          const { luminoWidget } = await IpylabModel.toLuminoWidget(value);
          setNestedProperty(content.kwgs, dottedname, luminoWidget);
        }
      }
    }
    if (content.toObject instanceof Array) {
      // Replace values in kwgs with attributes
      for (const dottedname of content.toObject) {
        const value = getNestedObject({
          base: content.kwgs,
          dottedname,
          nullIfMissing: false
        });
        if (value && typeof value === 'string') {
          const value_ = await IpylabModel.toObject(this.base, value);
          setNestedProperty(content.kwgs, dottedname, value_);
        }
      }
    }
    if (content.ipylab_FE) {
      // Result of an operation request in the backend.
      const op = this._pendingOperations.get(content.ipylab_FE);
      this._pendingOperations.delete(content.ipylab_FE);
      if (op) {
        if (content.error) {
          op.reject(new Error(content.error?.repr ?? content.error));
        } else {
          op.resolve(content.payload);
        }
      }
    } else if (content.ipylab_BE) {
      this._do_operation_for_backend(content);
    }
  }

  /**
   * Perform an operation for the backend returning the result if successful
   * or an 'error' message if unsuccessful.
   * Results are 'transformed' by the method specified in the call to the operation from the backend.
   * The transformed result is returned to the backend using the ipylab_BE value (uuid4).
   * @param content
   */
  private async _do_operation_for_backend(content: any) {
    const { operation, ipylab_BE, transform, kwgs } = content;
    try {
      let result, buffers;
      result = await this.operation(operation, kwgs);
      if ((result as any)?.buffers) {
        buffers = (result as any).buffers;
        delete (result as any).buffers;
      }
      if ((result as any)?.payload) {
        result = (result as any).payload;
      }
      const response = {
        ipylab_BE,
        operation,
        payload: (await this.transformObject(result, transform)) ?? null
      };
      this.send(response, null, buffers);
    } catch (e) {
      this.send({
        operation: operation,
        ipylab_BE: content.ipylab_BE,
        error: `${(e as Error).message}`
      });
      console.error(e);
    }
  }

  private async _executeMethod(payload: any): Promise<any> {
    const { dottedname, args } = payload;
    const obj = this.base;
    const ownername = dottedname.split('.').slice(0, -1).join('.');
    const owner = getNestedObject({ base: obj, dottedname: ownername });
    let func = getNestedObject({ base: obj, dottedname });
    func = func.bind(owner, ...args);
    return await func();
  }

  private _listProperties(payload: any) {
    const obj = getNestedObject({ ...payload, base: this.base });
    return listProperties({ ...payload, obj });
  }

  private _getProperty(payload: any) {
    return getNestedObject({ ...payload, base: this.base });
  }

  /**
   * Update the property. Equivalent to python: `dict.update`.
   */
  private async _updateProperty(payload: any): Promise<null> {
    const { value, valueTransform } = payload;
    const obj = this._getProperty(payload);
    const value_ = await this.transformObject(value, valueTransform);
    return Object.assign(obj, value_);
  }
  /**
   * Set a property. Equivalent to python `setattr`.
   */
  private async _setProperty(payload: any): Promise<any> {
    const { dottedname, value, valueTransform } = payload;
    const value_ = await this.transformObject(value, valueTransform);
    setNestedProperty(this.base, dottedname, value_);
    return value_;
  }

  /**
   * Schedule an operation to be performed on the backend.
   * This is a mirror of 'schedule_operation' on the backend.
   *
   * @param operation The name of the operation to perform on the backend.
   * @param payload Corresponding payload as expected by the backend.
   * @param transform The type of transformation to apply. See python `class Transform`.
   */
  async scheduleOperation(
    operation: string,
    payload: JSONValue,
    transform: any
  ): Promise<any> {
    const ipylab_FE = UUID.uuid4();
    // Create callbacks to be resolved when a custom message is received
    // with the key `ipylab_FE`.
    const opDone = new PromiseDelegate();
    this._pendingOperations.set(ipylab_FE, opDone);
    this.send({ ipylab_FE, operation, payload });
    const result: any = await opDone.promise;
    return await this.transformObject(result, transform);
  }

  /**
   * Perform an operation and return the result.
   *
   * @param op Name of the operation.
   * @param payload Options relevant to the operation.
   * @returns Raw result of the operation.
   */
  async operation(op: string, payload: any): Promise<any> {
    switch (op) {
      case 'executeCommand':
        return await this.commands.execute(payload.id, payload.args);
      case 'executeMethod':
        return await this._executeMethod(payload);
      case 'getProperty':
        return await this._getProperty(payload);
      case 'listProperties':
        return this._listProperties(payload);
      case 'setProperty':
        return this._setProperty(payload);
      case 'updateProperty':
        return this._updateProperty(payload);
      case 'newSessionContext':
        return await IpylabModel.newSessionContext(payload);
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
   * Transform the object for sending.
   * @param obj
   * @param args The mode as a string or an object with mode and any other parameters.
   * @returns
   */
  async transformObject(obj: any, args: string | any): Promise<any> {
    const transform = typeof args === 'string' ? args : args.transform;
    let result, func;
    let cid;

    switch (transform) {
      case 'raw':
        return (await obj) as any;
      case 'null':
        return null;
      case 'connection':
        cid = args?.cid ?? `ipylab-connection:${UUID.uuid4()}`;
        IpylabModel.registerConnection(cid, obj);
        if (args.auto_dispose) {
          IpylabModel.onKernelLost(this.kernel, obj.dispose, obj, true);
        }
        return { cid: cid, id: obj.id, info: args.info };
      case 'advanced':
        // expects args.mappings = {key:transform}
        result = new Object();
        for (const key of Object.keys(args.mappings)) {
          const base = getNestedObject({ base: obj, dottedname: key });
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
      case 'object':
        if (obj) {
          try {
            return await IpylabModel.toObject(null, obj);
          } catch {}
        }
        return obj;
      default:
        throw new Error(`Invalid return mode: '${transform}'`);
    }
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: 'IpylabModel',
      _model_module: IpylabModel.model_module,
      _model_module_version: IpylabModel.model_module_version,
      _view_name: null,
      _view_module: IpylabModel.view_module,
      _view_module_version: IpylabModel.view_module_version
    };
  }

  /**
   * Start a new session that support comms needed for iplab needs for comms.
   * @returns
   */
  static async newSessionContext({
    name,
    path = '',
    kernelId = '',
    language = 'python',
    code = '',
    type = 'console',
    ensureFrontend = true
  }: {
    name: string;
    path: string;
    kernelId?: string;
    language?: string;
    code?: string;
    type?: string;
    ensureFrontend?: boolean;
  }): Promise<SessionContext> {
    path = path || UUID.uuid4();

    const sessionContext = new SessionContext({
      sessionManager: IpylabModel.sessionManager,
      specsManager: IpylabModel.app.serviceManager.kernelspecs,
      path: path,
      name: name || path,
      type: type,
      kernelPreference: {
        id: kernelId || null,
        language: language,
      }
    });
    await sessionContext.initialize();
    if (!sessionContext.isReady) {
      await new SessionContextDialogs({
        translator: IpylabModel.translator
      }).selectKernel(sessionContext!);
    }
    if (!sessionContext.isReady) {
      sessionContext.dispose();
      throw new Error('Cancelling because a kernel was not provided');
    }
    const kernel = sessionContext.session.kernel;
    if (ensureFrontend) {
      await IpylabModel.ensureFrontend(kernel);
    }
    if (code) {
      await kernel.requestExecute({ code, store_history: false }).done;
    }
    return sessionContext;
  }

  /**
   * Send an evaluate request to a kernel using its JupyterFrontEndModel.
   * If the kernelId isn't found a new context will be started.
   * The user may be prompted to select a kernel.
   */
  static async evaluate(options: any): Promise<any> {
    let { kernelId } = options;
    if (!IpylabModel.jfemPromises.has(kernelId)) {
      const sc = await IpylabModel.newSessionContext(options);
      kernelId = sc.session.kernel.id;
    }
    const jfem = await IpylabModel.getFrontendModel(kernelId);
    return await jfem.scheduleOperation('evaluate', options, 'raw');
  }

  /**
   * Get the WidgetManger searching all known kernels.
   *
   * This blocks until the frontend is ready in the kernel.
   * @param model_id The widget model id
   * @returns
   */
  static async getWidgetManager(
    model_id: string,
    kernelId: string
  ): Promise<KernelWidgetManager> {
    if (kernelId) {
      const jfem = await IpylabModel.getFrontendModel(kernelId);
      if (jfem.widget_manager.has_model(model_id)) {
        return jfem.widget_manager;
      }
    }

    function* search_for_manager() {
      for (const kernelId of IpylabModel.jfemPromises.keys()) {
        yield (async () => {
          const jfem = await IpylabModel.getFrontendModel(kernelId, 10000);
          if (jfem.widget_manager.has_model(model_id)) {
            return jfem.widget_manager;
          }
          throw new Error(`WidgetManager not found in kernel: ${kernelId}`);
        })();
      }
    }
    search_for_manager;
    const result = await Promise.any(search_for_manager());
    if (result instanceof KernelWidgetManager) {
      return result;
    }
    throw new Error(`WidgetManager not found for model_id='${model_id}'`);
  }

  /**
   * Get the WidgetModel
   *
   * This depends on the PR requiring a per-kernel widget manager.
   *
   * @param model_id The model id
   * @returns WidgetModel
   */
  static async getWidgetModel(model_id: string, kernelId = '') {
    const manager = await IpylabModel.getWidgetManager(model_id, kernelId);
    const model: WidgetModel = await manager.get_model(model_id);
    return { model, kernelId: manager.kernel.id };
  }

  /**
   * Get a Lumino Widget searching extensively.
   *
   * @param id
   * @param kernelId The kernel where to start looking for widget models.
   * @returns
   */
  static async toLuminoWidget(id: string, kernelId = '') {
    let luminoWidget, manager;
    if (typeof id === 'string' && id) {
      if (id.slice(0, 10) === 'IPY_MODEL_') {
        const model_id = id.slice(10).split(':', 1)[0];
        manager = await IpylabModel.getWidgetManager(model_id, kernelId);
        const kernel = manager.kernel;
        const model = await manager.get_model(model_id);
        luminoWidget = (await manager.create_view(model, {})).luminoWidget;
        IpylabModel.onKernelLost(kernel, luminoWidget.dispose, luminoWidget);
      } else {
        luminoWidget = await IpylabModel.fromConnectionOrId(id);
      }
      if (luminoWidget instanceof Widget) {
        return { luminoWidget, kernelId: kernelId };
      }
    }
    throw new Error(`Unable to generate a Widget for id='${id}'`);
  }

  /**
   * Get the lumino widget from the shell using its id.
   *
   * @param id
   * @returns
   */
  static getLuminoWidgetFromShell(id: string) {
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

  static async ensureFrontend(kernel: Kernel.IKernelConnection) {
    if (!IpylabModel.jfemPromises.has(kernel.id)) {
      IpylabModel.jfemPromises.set(kernel.id, new PromiseDelegate());
      const manager = new KernelWidgetManager(kernel, IpylabModel.rendermime);
      await kernel.requestExecute(
        {
          code: 'import ipylab',
          store_history: false
        },
        true
      ).done;
      if (!manager.restoredStatus) {
        await new Promise(resolve => manager.restored.connect(resolve));
      }
    }
    return await IpylabModel.jfemPromises.get(kernel.id).promise;
  }

  static async getFrontendModel(kernelId: string, timeout = 100000) {
    await this.backend_ready.promise;
    if (!IpylabModel.jfemPromises.has(kernelId)) {
      const model = await IpylabModel.kernelManager.findById(kernelId);
      if (!model) {
        throw new Error(`Kernel doesn't exist ${kernelId}`);
      }
      const kernel = IpylabModel.kernelManager.connectTo({ model });
      await IpylabModel.ensureFrontend(kernel);
    }
    const delegate = IpylabModel.jfemPromises.get(kernelId);
    const t = setTimeout(() => {
      IpylabModel.jfemPromises.delete(kernelId);
      delegate.reject(
        `Timed out waiting for JupyterFrontEndModel to load for kernelId ='${kernelId}'`
      );
    }, timeout);
    const jfem = await delegate.promise;
    clearTimeout(t);
    return jfem;
  }

  /**
   *
   * @param cid Get an object that has been registered as a connection.
   * @returns
   */
  static async fromConnectionOrId(cid: string, id: string = ''): Promise<any> {
    if (IpylabModel.connections.has(cid)) {
      return IpylabModel.connections.get(cid);
    }
    if (id.slice(0, 10) === 'IPY_MODEL_') {
      const model_id = id.slice(10);
      return (await IpylabModel.getWidgetModel(model_id)).model;
    } else {
      return IpylabModel.getLuminoWidgetFromShell(id || cid);
    }
  }

  /**
   *Keep a reference to an object so it can be found from the backend.
   * @param obj
   */
  static registerConnection(cid: string, obj: any) {
    if (!cid) {
      throw new Error('`cid` not provided!');
    }
    if (typeof obj !== 'object') {
      throw new Error(`An object is required but got a '${typeof obj}'`);
    }
    const obj_ = Private.connections.get(cid);
    if (obj_ && obj_ !== obj) {
      throw new Error(
        `Another object with cid='${cid}' is already registered!`
      );
    }
    if (!obj.dispose) {
      obj.dispose = () => '';
      obj.ipylabDisposeOnClose = true;
    }
    Private.connections.set(cid, obj);
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
    obj.disposed.connect(() => Private.connections.delete(cid));
  }

  /**
   * Returns the object for the dottedname 'value'.
   * 1. If value starts with IPY_MODEL_ it will ignore the base, instead
   *    unpacking the model and return the object relative to dottedname after
   *    the model name. If there is no path after the model id it will be the model.
   * 2. The object as specified by the dottedname relate to the base will be returned.
   * 3. An error will be thrown if the value doesn't point an existing attribute.
   *
   * @param base The object to locate the dotted value.
   * @param value The dottedname on the base (except for IPY_MODEL_).
   * @param nullIfMissing Return a null instead of throwing an error if missing.
   */
  static async toObject(
    base: any,
    value: any,
    nullIfMissing = false
  ): Promise<any> {
    if (typeof value === 'string') {
      let dottedname = value;
      if (value.slice(0, 10) === 'IPY_MODEL_') {
        let model_id;
        [model_id, dottedname] = value.slice(10).split('.', 2);
        base = (await IpylabModel.getWidgetModel(model_id)).model;
        if (base.isConnectionModel) {
          base = base.base;
        }
      }
      return await getNestedObject({
        base,
        dottedname: dottedname ?? '',
        nullIfMissing
      });
    }
    if (value?.OTHER_PROPERTIES?.cid) {
      return await IpylabModel.fromConnectionOrId(value.OTHER_PROPERTIES.cid);
    }
    throw new Error(`Cannot convert this value to an object: ${value}`);
  }

  /**
   * Call slot when kernel is restarting or dead.
   *
   * As soon as the kernel is restarted, all Python objects are lost. Use this
   * function to close the corresponding frontend objects.
   * @param kernel
   * @param slot
   * @param thisArg
   * @param onceOnly -  [true] Once called the slot will be disconnected.
   */
  static onKernelLost(
    kernel: Kernel.IKernelConnection,
    slot: any,
    thisArg?: any,
    onceOnly = true
  ) {
    const id = kernel.id;
    if (!Private.kernelLostSlot.has(id)) {
      kernel.statusChanged.connect(_onKernelStatusChanged);
      Private.kernelLostSlot.set(id, new Signal<any, null>(kernel));
      kernel.disposed.connect(() => {
        Private.kernelLostSlot.get(id).emit(null);
        Signal.clearData(Private.kernelLostSlot.get(id));
        Private.kernelLostSlot.delete(id);
        kernel.statusChanged.disconnect(_onKernelStatusChanged);
      });
    }
    const callback = () => {
      slot.bind(thisArg)();
      if (onceOnly) {
        Private.kernelLostSlot.get(id)?.disconnect(callback);
      }
    };
    Private.kernelLostSlot.get(id).connect(callback);
  }

  /**
   * Promises to frontends that may be loading.
   */
  static get jfemPromises() {
    return Private.jfemPromises;
  }
  static get connections() {
    return Private.connections;
  }

  static get kernelManager(): Kernel.IManager {
    return IpylabModel.app.serviceManager.kernels;
  }

  static get sessionManager(): Session.IManager {
    return IpylabModel.app.serviceManager.sessions;
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  widget_manager: KernelWidgetManager;
  private _pendingOperations = new Map<string, PromiseDelegate<any>>();
  private _base: object | null;
  static model_name: string = 'IpylabModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_module: string;
  static view_module_version = MODULE_VERSION;
  static initial_load: boolean;
  static backend_ready = new PromiseDelegate();
  static app: JupyterFrontEnd;
  static rendermime: IRenderMimeRegistry;
  static labShell: LabShell;
  static defaultBrowser: IDefaultFileBrowser;
  static palette: ICommandPalette;
  static translator: ITranslator;
  static launcher: ILauncher;
  static menu: IMainMenu;
  static exports: IWidgetRegistryData;
  static connection_model_name = 'ConnectionModel';
  static tracker = new WidgetTracker<Widget>({ namespace: 'ipylab' });
}

/**
 * React to changes to the kernel status.
 */
function _onKernelStatusChanged(kernel: Kernel.IKernelConnection) {
  if (['dead', 'restarting'].includes(kernel.status)) {
    Private.kernelLostSlot.get(kernel.id).emit(null);
  }
}

/**
 * A namespace for private data
 */
namespace Private {
  export const connections = new Map<string, IObservableDisposable>();
  export const jfemPromises = new Map<
    string,
    PromiseDelegate<JupyterFrontEndModel>
  >();
  export const kernelLostSlot = new ObservableMap<
    Signal<Kernel.IKernelConnection, null>
  >();
}
