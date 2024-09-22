// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { DOMUtils, SessionContext } from '@jupyterlab/apputils';
import { ObservableMap } from '@jupyterlab/observables';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel } from '@jupyterlab/services';
import { Signal } from '@lumino/signaling';
import { IpylabModel } from './ipylab';

/**
 * Start a new session that support comms needed for iplab needs for comms.
 * @returns
 */
export async function newSessionContext({
  name,
  path,
  rendermime,
  kernelId = '',
  language = 'python3',
  code = '',
  type = 'console'
}: {
  name: string;
  path: string;
  rendermime?: IRenderMimeRegistry;
  kernelId?: string;
  language?: string;
  code?: string;
  type?: string;
}): Promise<SessionContext> {
  const sessionContext = new SessionContext({
    sessionManager: IpylabModel.app.serviceManager.sessions,
    specsManager: IpylabModel.app.serviceManager.kernelspecs,
    path: path,
    name: name ?? path,
    type: type,
    kernelPreference: {
      id: kernelId || DOMUtils.createDomID(),
      language: language
    }
  });
  await sessionContext.initialize();
  await sessionContext.ready;

  // Create a manager for the kernel to support widgets.
  // The pull request at this link enables widgets to work without requiring a document or console to remain open:
  //  https://github.com/jupyter-widgets/ipywidgets/pull/3922

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
  return sessionContext;
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
export function getNestedObject({
  base,
  path,
  nullIfMissing = false,
  basename = ''
}: {
  base: object;
  path: string;
  nullIfMissing?: boolean;
  basename?: string;
}): any {
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
    if (nullIfMissing) {
      return null;
    }
    throw new Error(
      `Failed to get the attribute '${attr}' in the nested path '${path}'.` +
        (basename ? ` from the base '${basename}'` : '')
    );
  }
  return obj;
}

/**
 * Set a nested attribute relative to the base
 * @param base
 * @param path
 * @param value
 */
export function setNestedAttribute(
  base: object,
  path: string,
  value: any,
  basename: string = ''
) {
  const obj = getNestedObject({
    base: base,
    path: path.split('.').slice(0, -1).join('.'),
    basename: basename
  });
  obj[path.split('.').slice(-1)[0]] = value;
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
 * Provide a list of all attributes belonging to obj.
 *
 * @param obj Any object.
 * @returns
 */
export function findAllProperties({
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
  return findAllProperties({
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
export function listProperties({
  obj,
  type = '',
  depth = 1
}: {
  obj: any;
  type?: string;
  depth?: number;
}) {
  return findAllProperties({ obj, items: [], type, depth }).map(p => ({
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
