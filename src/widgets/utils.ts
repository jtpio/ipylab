// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { SessionContext } from '@jupyterlab/apputils';
import { ObservableMap } from '@jupyterlab/observables';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel, Session } from '@jupyterlab/services';
import { UUID } from '@lumino/coreutils';
import { Signal } from '@lumino/signaling';
import { IpylabModel, JSONObject, JSONValue } from './ipylab';
/**
 * Start a new session that support comms needed for iplab needs for comms.
 * @returns
 */
export async function newSession({
  name,
  path,
  rendermime,
  kernelId = '',
  language = 'python3',
  code = '',
  type = 'Ipylab'
}: {
  name: string;
  path: string;
  rendermime?: IRenderMimeRegistry;
  kernelId?: string;
  language?: string;
  code?: string;
  type?: string;
}): Promise<Session.ISessionConnection> {
  const sessionContext = new SessionContext({
    sessionManager: IpylabModel.app.serviceManager.sessions,
    specsManager: IpylabModel.app.serviceManager.kernelspecs,
    path: path,
    name: name ?? path,
    type: type,
    kernelPreference: {
      id: kernelId || `${UUID.uuid4()}`,
      language: language
    }
  });
  await sessionContext.initialize();
  await sessionContext.ready;

  // Create a manager for the kernel. It will stay alive for the life of the kernel.
  // Requires https://github.com/jupyter-widgets/ipywidgets/pull/3922 to be adopted.
  new KernelWidgetManager(sessionContext.session.kernel, rendermime as any);
  if (code) {
    const future = sessionContext.session.kernel.requestExecute(
      {
        code: code,
        store_history: false
      },
      false
    );
    await future.done;
    future.dispose();
  }
  return sessionContext.session;
}

export async function newNotebook({
  name,
  path,
  kernelId,
  kernelName = 'python3'
}: {
  name: string;
  path: string;
  kernelId: string;
  kernelName?: string;
}): Promise<JSONValue> {
  const nb = await IpylabModel.app.commands.execute('notebook:create-new', {
    kernelId: kernelId || `${UUID.uuid4()}`,
    kernelName: kernelName
  });
  await nb.sessionContext.ready;
  if (name) {
    await nb.sessionContext.session.setName(name);
  }
  if (path) {
    await nb.sessionContext.session.setPath(path);
  }
  return nb;
}

/**Inject code into the kernel.
 * @param payload.kernelId : Normally kernel.id
 * @param payload.code : code to inject
 * @returns
 */
export async function injectCode({
  kernelId,
  code,
  user_expressions
}: {
  kernelId: string;
  code: string;
  user_expressions?: JSONObject;
}): Promise<JSONValue> {
  const kernelModel = await IpylabModel.app.serviceManager.kernels.findById(
    kernelId
  );
  const connection = IpylabModel.app.serviceManager.kernels.connectTo({
    model: kernelModel
  });
  const future = connection.requestExecute({
    code: code,
    store_history: false,
    stop_on_error: true,
    silent: true,
    allow_stdin: false,
    user_expressions: user_expressions
  });
  const result = (await future.done) as any;
  if (result.content.status === 'ok') {
    return result.content.payload;
  } else {
    throw new Error(
      `Execution status = ${result.status} not 'ok' traceback=${result.content.traceback}`
    );
  }
}

/**
 *Returns a nested object relative to `this`.
 * @param base The starting object.
 * @param path The dotted path of the object.
 * @returns
 */

/**
 * Get the nested object of base at path.
 * @param base Starting object
 * @param path Dotted path to an object below base
 * @returns
 */
export function getNestedObject(base: object, path: string): any {
  let obj: object = base;
  let path_ = '';
  const parts = path.split('.');
  let attr = '';
  for (let i = 0; i < parts.length; i++) {
    attr = parts[i];
    if (attr in obj) {
      obj = obj[attr as keyof typeof obj];
      path_ = !path_ ? attr : `${path_}.${attr}`;
    } else {
      break;
    }
  }
  if (path_ !== path) {
    throw new Error(
      `Failed to get the nested attribute ${path_}.${attr} ` +
        ` (base='${(base as any).name ?? 'unknown'}') `
    );
  }
  return obj;
}

/**
 * Convert a string definition of a function to a function object.
 * @param code The function as a string: eg. 'function (a, b) { return a + b; }'
 * @returns
 */
export function toFunction(code: string) {
  return new Function('return ' + code)();
}

/**
 * Transform the object for sending.
 * TODO: Add in 'function'
 * @param obj
 * @param options The mode as a string or an object with mode and any other parameters.
 * @param thisArg 'function' mode only - the binding of `this`.
 * @returns
 */
export async function transformObject(
  obj: any,
  options: string | any,
  thisArg: object = null
): Promise<JSONValue> {
  const mode = typeof options === 'string' ? options : options.mode;

  let path: string, transform: string, result, part: string, func;

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
      result = new Object();
      for (let i = 0; i < options.parts.length; i++) {
        if (typeof options.parts[i] === 'string') {
          path = options.parts[i];
          transform = 'raw';
        } else {
          path = options.parts[i].path;
          transform = options.parts[i].transform;
        }
        part = getNestedObject(obj, path);
        (result as any)[path] = await transformObject(part, transform);
      }
      return result as any;
    case 'function':
      func = toFunction(options.code).bind(thisArg);
      if (func.constructor.name === 'AsyncFunction') {
        return await func(obj);
      }
      return func(obj);
    default:
      throw new Error(`Invalid return mode: '${options.mode}'`);
  }
}

/**
 * Provide a list of all methods belonging to obj.
 *
 * @param obj Any object.
 * @returns
 */
export function findAllAttributes({
  obj,
  items = [],
  type = '',
  depth = 1
}: {
  obj: any;
  items?: Array<string>;
  type?: string;
  depth?: number;
}): Array<string> {
  if (!obj || depth === 0) {
    return [...new Set(items)];
  }

  const props = Object.getOwnPropertyNames(obj);
  return findAllAttributes({
    obj: Object.getPrototypeOf(obj),
    items: [...items, ...props],
    type,
    depth: depth - 1
  });
}

/**
 * Returns a mapping of types and names for obj.
 * @param obj Any object
 * @returns
 */
export function listAttributes({
  obj,
  type = '',
  depth = 1
}: {
  obj: any;
  type?: string;
  depth?: number;
}) {
  return findAllAttributes({ obj, items: [], type, depth }).map(p => ({
    name: p,
    type: typeof obj[p]
  }));
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
export function onKernelLost(
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
  export const kernelLostSlot = new ObservableMap<
    Signal<Kernel.IKernelConnection, null>
  >();
}
