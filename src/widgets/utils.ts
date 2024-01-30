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
