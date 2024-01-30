// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { UUID } from '@lumino/coreutils';
import { IpylabModel, JSONValue } from './ipylab';
import { Session } from '@jupyterlab/services';
import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import { SessionContext } from '@jupyterlab/apputils';
// import { Signal } from '@lumino/signaling';
import * as base from '@jupyter-widgets/base';
import { JUPYTER_CONTROLS_VERSION } from '@jupyter-widgets/controls/lib/version';
import {
  OutputModel,
  OutputView,
  OUTPUT_WIDGET_VERSION
} from '@jupyter-widgets/output';

export async function newSession({
  name,
  path,
  kernelId = '',
  language = 'python3',
  code = ''
}: {
  name: string;
  path: string;
  kernelId?: string;
  language?: string;
  code?: string;
}): Promise<Session.ISessionConnection> {
  const sessionContext = new SessionContext({
    sessionManager: IpylabModel.app.serviceManager.sessions,
    specsManager: IpylabModel.app.serviceManager.kernelspecs,
    path: path,
    name: name,
    type: 'ipylab',
    kernelPreference: {
      id: kernelId || `${UUID.uuid4()}`,
      language: language
    }
  });
  await sessionContext.initialize();
  await sessionContext.ready;

  const session = sessionContext.session;
  const manager = new KernelWidgetManager(
    session.kernel,
    IpylabModel.rendermime
  );

  registerWidgets(manager);

  if (code) {
    const future = session.kernel.requestExecute(
      {
        code: code,
        store_history: false
      },
      false
    );
    await future.done;
    future.dispose();
  }
  return session;
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
  if (name) await nb.sessionContext.session.setName(name);
  if (path) await nb.sessionContext.session.setPath(path);
  return nb;
}

/**
 * @param payload.kernelId
 * @param payload.code : code to inject
 * @returns
 */
export async function injectCode({
  kernelId,
  code
}: {
  kernelId: string;
  code: string;
}): Promise<JSONValue> {
  const kernelModel = await IpylabModel.app.serviceManager.kernels.findById(
    kernelId
  );
  const connection = IpylabModel.app.serviceManager.kernels.connectTo({
    model: kernelModel
  });
  const future = connection.requestExecute({
    code: code,
    store_history: false
  });
  return (await future.done) as any;
}

/**
 * Manually register known widgets.
 * TODO: use the JuperWidgetRegistry for models instead.
 *
 * @param manager The new manager
 */
function registerWidgets(manager: KernelWidgetManager) {
  manager.register(IpylabModel.exports);
  manager.register({
    name: '@jupyter-widgets/base',
    version: base.JUPYTER_WIDGETS_VERSION,
    exports: {
      WidgetModel: base.WidgetModel,
      WidgetView: base.WidgetView,
      DOMWidgetView: base.DOMWidgetView,
      DOMWidgetModel: base.DOMWidgetModel,
      LayoutModel: base.LayoutModel,
      LayoutView: base.LayoutView,
      StyleModel: base.StyleModel,
      StyleView: base.StyleView,
      ErrorWidgetView: base.ErrorWidgetView
    }
  });
  manager.register({
    name: '@jupyter-widgets/controls',
    version: JUPYTER_CONTROLS_VERSION,
    exports: () => {
      return new Promise((resolve, reject) => {
        (require as any).ensure(
          ['@jupyter-widgets/controls'],
          (require: NodeRequire) => {
            // eslint-disable-next-line @typescript-eslint/no-var-requires
            resolve(require('@jupyter-widgets/controls'));
          },
          (err: any) => {
            reject(err);
          },
          '@jupyter-widgets/controls'
        );
      });
    }
  });

  manager.register({
    name: '@jupyter-widgets/output',
    version: OUTPUT_WIDGET_VERSION,
    exports: { OutputModel, OutputView }
  });
}

/**
 *Returns a nested object relative to `this`.
 * @param base The starting object.
 * @param path The dotted path of the object.
 * @returns
 */

export function getNestedObject(base: object, path: string): any {
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
 * Convert a string definition of a function to a function object.
 * @param code The function as a string: eg. 'function (a, b) { return a + b; }'
 * @returns
 */
export function toFunction(code: string): Function {
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
export function transformObject(
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
        var part = getNestedObject(obj, path);
        result[path] = transformObject(part, transform);
      }
      return result;
    case 'function':
      var func = toFunction(options.code).bind(thisArg);
      return func(obj);
    default:
      throw new Error(`Invalid return mode: '${options.mode}'`);
  }
}
