// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { KernelWidgetManager } from '@jupyter-widgets/jupyterlab-manager';
import {
  DOMUtils,
  InputDialog,
  MainAreaWidget,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { FileDialog } from '@jupyterlab/filebrowser';
import { IMainMenu, MainMenu } from '@jupyterlab/mainmenu';
import { PromiseDelegate } from '@lumino/coreutils';
import {
  IDisposable,
  ISerializers,
  IpylabModel,
  JSONValue,
  Widget
} from './ipylab';
import { newSessionContext } from './utils';
export class JupyterFrontEndModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name
    };
  }

  /**
   * Initialize a JupyterFrontEndModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  async initialize(attributes: any, options: any): Promise<void> {
    const kernelId = options.widget_manager.kernel.id;
    if (!Private.jupyterFrontEndModels.has(options.widget_manager.kernel.id)) {
      Private.jupyterFrontEndModels.set(kernelId, new PromiseDelegate());
    }
    await super.initialize(attributes, options);
    this.set('version', this.app.version);
    this.sessionManager.runningChanged.connect(
      this._updateAllSessionDetails,
      this
    );
    if (this.labShell) {
      this.labShell.currentChanged.connect(this._updateSessionDetails, this);
      this.labShell.activeChanged.connect(this._updateSessionDetails, this);
      this._updateSessionDetails();
    }
    this._updateAllSessionDetails();
    Private.jupyterFrontEndModels.get(kernelId).resolve(this);
  }

  close(comm_closed?: boolean): Promise<void> {
    Private.jupyterFrontEndModels.delete(this.kernelId);
    this.labShell.currentChanged.disconnect(this._updateSessionDetails, this);
    this.labShell.activeChanged.disconnect(this._updateSessionDetails, this);
    this.sessionManager.runningChanged.disconnect(
      this._updateAllSessionDetails,
      this
    );
    return super.close(comm_closed);
  }

  private _updateSessionDetails(): void {
    const currentWidget = this.shell.currentWidget as any;
    const current_session = currentWidget?.sessionContext?.session?.model ?? {};
    if (this.get('current_widget_id') !== currentWidget?.id) {
      this.set('current_widget_id', currentWidget?.id ?? '');
      this.set('current_session', current_session);
      this.save_changes();
    }
  }
  private _updateAllSessionDetails(): void {
    this.set('all_sessions', Array.from(this.sessionManager.running()));
    this.save_changes();
  }

  updateTrackerInfo() {
    const settings = IpylabModel.tracker
      .filter(widget => true)
      .flatMap(widget => (widget as any).ipylabSettings);
    this.set('all_shell_connections_info', settings);
    this.save_changes();
  }

  async operation(op: string, payload: any): Promise<JSONValue | IDisposable> {
    function _get_result(result: any): any {
      if (result.value === null) {
        throw new Error('Cancelled');
      }
      return result.value;
    }
    let result;
    switch (op) {
      case 'showDialog':
        result = await showDialog(payload);
        return { value: result.button.accept, isChecked: result.isChecked };
      case 'getBoolean':
        return await InputDialog.getBoolean(payload).then(_get_result);
      case 'getItem':
        return await InputDialog.getItem(payload).then(_get_result);
      case 'getNumber':
        return await InputDialog.getNumber(payload).then(_get_result);
      case 'getText':
        return await InputDialog.getText(payload).then(_get_result);
      case 'getPassword':
        return await InputDialog.getPassword(payload).then(_get_result);
      case 'showErrorMessage':
        await showErrorMessage(payload.title, payload.error, payload.buttons);
        return IpylabModel.OPERATION_DONE;
      case 'getOpenFiles':
        payload.manager = this.defaultBrowser.model.manager;
        return await FileDialog.getOpenFiles(payload).then(_get_result);
      case 'getExistingDirectory':
        payload.manager = this.defaultBrowser.model.manager;
        return await FileDialog.getExistingDirectory(payload).then(_get_result);
      case 'newSessionContext':
        return await newSessionContext(payload);
      case 'generateMenu':
        return this._generateMenu(payload.options);
      case 'execEval':
        return await this._execEval(payload);
      case 'backend_ready':
        JupyterFrontEndModel.backend_ready.resolve(null);
      case 'startIyplabPythonBackend':
        return (await IpylabModel.ipylabKernel.checkStart(
          payload.restart ?? false
        )) as any;
      case 'shutdownKernel':
        if (payload.kernelId) {
          await this.commands.execute('kernelmenu:shutdown', {
            id: payload.kernelId
          });
        } else {
          this.kernel.shutdown();
        }
        return null;
      default:
        return await super.operation(op, payload);
    }
  }

  static async getFrontendModel(kernelId: string) {
    if (!Private.jupyterFrontEndModels.has(kernelId)) {
      Private.jupyterFrontEndModels.set(kernelId, new PromiseDelegate());
      const model =
        await IpylabModel.app.serviceManager.kernels.findById(kernelId);
      if (!model) {
        throw new Error(`Kernel doesn't exist ${kernelId}`);
      }
      const kernel = IpylabModel.app.serviceManager.kernels.connectTo({
        model
      });
      if (kernel.hasComm) {
        new KernelWidgetManager(kernel, IpylabModel.rendermime);
      }
      kernel.requestExecute(
        {
          code: 'import ipylab; ipylab.JupyterFrontEnd()',
          store_history: false
        },
        true
      );
    }
    return await Private.jupyterFrontEndModels.get(kernelId).promise;
  }

  /**
   * Add a widget to the application shell.
   *
   * It can handle ipywidgets and nativive MainAreaWidgets.
   * and can be used to move widgets about the shell. A factory can be specified
   * as mapping of 'id' and 'args'. The facto
   *
   * If factory is specified, it should include 'id' and 'args'.
   *
   * Ipywidgets are tracked making it is possible to refresh the page and change
   * workspaces. Changing a worksace that doesn't have the same object will
   * lose the connection. Define a factory to enable the connection to be restored.
   *
   * @param payload The payload to add
   */
  static async addToShell(payload: any): Promise<Widget> {
    let { kernelId, cid, area, options, factory } = payload;
    const model_id = cid.slice(cid.lastIndexOf(':') + 1);
    let luminoWidget;
    if (!cid) {
      cid = `ipylab-shell-connection:${DOMUtils.createDomID()}`;
    }
    const jfem = await JupyterFrontEndModel.getFrontendModel(kernelId);
    if (jfem.hasConnection(cid)) {
      luminoWidget = await jfem.toLuminoWidget(cid);
    } else if (factory) {
      luminoWidget = await IpylabModel.app.commands.execute(
        factory.id,
        factory.args
      );
    } else {
      luminoWidget = await jfem.toLuminoWidget(model_id);
    }
    if (
      (area === 'main' && !(luminoWidget instanceof MainAreaWidget)) ||
      typeof luminoWidget.title === 'undefined'
    ) {
      luminoWidget = new MainAreaWidget({
        content: luminoWidget as any
      }) as any;
      luminoWidget.node.removeChild(luminoWidget.toolbar.node);
    }
    if (!luminoWidget.id) {
      luminoWidget.id = cid;
    }
    const id = luminoWidget.id;
    luminoWidget.ipylabSettings = { kernelId, cid, id, area, options, factory };
    IpylabModel.registerConnection(luminoWidget, cid);
    IpylabModel.app.shell.add(luminoWidget as any, area, options);
    if (!IpylabModel.tracker.has(luminoWidget)) {
      if (model_id.slice(0, 10) === 'IPY_MODEL_') {
        // We add ipywidgets so they can be restored, other widgets should have their own tracker.
        IpylabModel.tracker.add(luminoWidget);
        jfem.updateTrackerInfo();
        luminoWidget.disposed.connect(() => jfem.updateTrackerInfo());
      } else {
        IpylabModel.tracker.inject(luminoWidget);
      }
    }
    return luminoWidget;
  }

  /**
   *Send an execEval request to another kernel using its JupyterFrontEndModel.
   */
  private async _execEval(payload: any): Promise<any> {
    const { kernelId, frontendTransform } = payload;
    const jfem = await JupyterFrontEndModel.getFrontendModel(kernelId);
    return await jfem.scheduleOperation('execEval', payload, frontendTransform);
  }

  private _generateMenu(options: IMainMenu.IMenuOptions) {
    const menu = MainMenu.generateMenu(
      this.commands,
      options,
      this.translator.load('jupyterlab')
    );
    return menu;
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };
  static model_name = 'JupyterFrontEndModel';
  static backend_ready = new PromiseDelegate();
}

/**
 * A namespace for private data
 */
namespace Private {
  export const jupyterFrontEndModels = new Map<
    string,
    PromiseDelegate<JupyterFrontEndModel>
  >();
}
