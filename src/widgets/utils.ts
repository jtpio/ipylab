// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { SessionContext, SessionContextDialogs } from '@jupyterlab/apputils';
import { ObservableMap } from '@jupyterlab/observables';
import { Kernel } from '@jupyterlab/services';
import { Signal } from '@lumino/signaling';
import { IpylabModel } from './ipylab';
import { UUID } from '@lumino/coreutils';
/**
 * Start a new session that support comms needed for iplab needs for comms.
 * @returns
 */
export async function newSessionContext({
  name,
  path = '',
  kernelId = '',
  language = 'python3',
  code = '',
  type = 'console'
}: {
  name: string;
  path: string;
  kernelId?: string;
  language?: string;
  code?: string;
  type?: string;
}): Promise<SessionContext> {
  path = path || UUID.uuid4();

  // TODO: Search for path first
  // if (!kernelId || !(await IpylabModel.kernelManager.findById(kernelId))) {
  // }

  const sessionContext = new SessionContext({
    sessionManager: IpylabModel.sessionManager,
    specsManager: IpylabModel.app.serviceManager.kernelspecs,
    path: path,
    name: name || path,
    type: type,
    kernelPreference: {
      id: kernelId || null,
      language: language
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
  // Create a manager for the kernel to support widgets.
  // The pull request at this link enables widgets to work without requiring a document or console to remain open:
  //  https://github.com/jupyter-widgets/ipywidgets/pull/3922
  new KernelWidgetManager(kernel, IpylabModel.rendermime);
  if (code) {
    await kernel.requestExecute({ code, store_history: false }).done;
  }
  return sessionContext;
}

/**
 *Returns a nested object relative to `base`.
 * @param base The starting object.
 * @param dottedname The dotted path to the object.
 * @returns
 */

export function getNestedObject({
  base,
  dottedname,
  nullIfMissing = false
}: {
  base: object;
  dottedname: string;
  nullIfMissing?: boolean;
}): any {
  let obj: object = base;
  let dottedname_ = '';
  const parts = dottedname.split('.');
  let attr = '';
  for (let i = 0; i < parts.length; i++) {
    attr = parts[i];
    if (attr in obj) {
      obj = obj[attr as keyof typeof obj];
      dottedname_ = !dottedname_ ? attr : `${dottedname_}.${attr}`;
    } else {
      break;
    }
  }
  if (dottedname_ !== dottedname) {
    if (nullIfMissing) {
      return null;
    }
    throw new Error(`Failed to get the object for dottedname='${dottedname}'`);
  }
  return obj;
}

/**
 * Set a nested property relative to the base
 * @param base The object
 * @param dottedname The dotted path of the property to set
 * @param value The value to set as the property
 */
export function setNestedProperty(
  base: object,
  dottedname: string,
  value: any
) {
  const obj = getNestedObject({
    base: base,
    dottedname: dottedname.split('.').slice(0, -1).join('.')
  });
  obj[dottedname.split('.').slice(-1)[0]] = value;
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
 * Provide an object detailing objects in obj.
 *
 * omitHidden: Will omit properties starting with '_'
 *
 * @param obj Any object.
 * @returns
 */
export function findAllProperties({
  obj,
  items = [],
  type = '',
  depth = 1,
  omitHidden = false
}: {
  obj: any;
  items?: Array<string>;
  type?: string;
  depth?: number;
  omitHidden?: boolean;
}): Array<string> {
  if (!obj || depth === 0) {
    return [...new Set(items)];
  }

  const props = Object.getOwnPropertyNames(obj).filter(value =>
    omitHidden ? value.slice(0, 1) !== '_' : true
  );
  return findAllProperties({
    obj: Object.getPrototypeOf(obj),
    items: [...items, ...props],
    type,
    depth: depth - 1,
    omitHidden: omitHidden
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
  depth = 1,
  omitHidden = false
}: {
  obj: any;
  type?: string;
  depth?: number;
  omitHidden?: boolean;
}): any {
  const out: any = {};
  for (const name of findAllProperties({
    obj,
    items: [],
    type,
    depth,
    omitHidden
  })) {
    const obj_ = obj[name];
    let type_: string = typeof obj_;
    let val: any = name;
    switch (type_) {
      case 'string':
      case 'number':
      case 'bigint':
      case 'boolean':
        out[name] = obj_;
        break;
      case 'undefined':
        out[name] = null;
      case 'object':
        if (obj_ instanceof Promise) {
          type_ = 'Promise';
          break;
        } else if (obj_ instanceof Signal) {
          type_ = 'Signal';
        }
        if (depth > 1) {
          val = {};
          val[name] = listProperties({ obj: obj_, type, depth: 1, omitHidden });
        }
      default:
        if (!out[`<${type_}s>`]) {
          out[`<${type_}s>`] = [val];
        } else {
          out[`<${type_}s>`].push(val);
          out[`<${type_}s>`] = out[`<${type_}s>`].sort();
        }
    }
  }
  // Sort alphabetically
  return Object.fromEntries(Object.entries(out).sort());
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
