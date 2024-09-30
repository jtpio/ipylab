// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import {
  InputDialog,
  MainAreaWidget,
  showDialog,
  showErrorMessage
} from '@jupyterlab/apputils';
import { FileDialog } from '@jupyterlab/filebrowser';
import { IMainMenu, MainMenu } from '@jupyterlab/mainmenu';
import { PromiseDelegate, UUID } from '@lumino/coreutils';
import { IpylabBackendModel } from './backend';
import { IpylabModel, Widget } from './ipylab';
import { newSessionContext } from './utils';

export class JupyterFrontEndModel extends IpylabModel {
  async ipylabInit(base: any = null) {
    if (!IpylabModel.jfemPromises.has(this.kernelId)) {
      IpylabModel.jfemPromises.set(this.kernelId, new PromiseDelegate());
    }
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
    await super.ipylabInit(base);
    IpylabModel.jfemPromises.get(this.kernelId).resolve(this);
  }

  close(comm_closed?: boolean): Promise<void> {
    IpylabModel.jfemPromises.delete(this.kernelId);
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
    if (this.get('all_shell_connections_info') !== settings) {
      this.set('all_shell_connections_info', settings);
      this.save_changes();
    }
  }

  async operation(op: string, payload: any): Promise<any> {
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
        return await showErrorMessage(
          payload.title,
          payload.error,
          payload.buttons
        );
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
      case 'evaluate':
        return await JupyterFrontEndModel.evaluate(payload);
      case 'startIyplabPythonBackend':
        return (await IpylabBackendModel.checkStart(
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

  private _generateMenu(options: IMainMenu.IMenuOptions) {
    const menu = MainMenu.generateMenu(
      this.commands,
      options,
      this.translator.load('jupyterlab')
    );
    return menu;
  }

  /**
   * Provided for IpylabModel.tracker for restoring widgets to the main area.
   * @param args `ipylabSettings` in 'addToShell'
   */
  static async restoreToShell(args: any): Promise<Widget> {
    if (
      !args.kernelId ||
      !(await IpylabModel.kernelManager.findById(args.kernelId))
    ) {
      return;
    }
    return JupyterFrontEndModel.addToShell(args);
  }

  /**
   * Add any widget to the application shell.
   *
   * It can handle ipywidgets and native MainAreaWidgets.
   * and can be used to move widgets about the shell. A factory can be specified
   * as mapping of 'id' and 'args'. The facto
   *
   * If factory is specified, it should include 'id' and 'args'.
   *
   * Ipywidgets are tracked making it is possible to refresh the page and change
   * workspaces. Changing a worksace that doesn't have the same object will
   * lose the connection. Define a factory to enable the connection to be restored.
   *
   * @param args The payload to add
   */
  static async addToShell(args: any): Promise<Widget> {
    let { area, options, cid, kernelId } = args;
    let luminoWidget: Widget | MainAreaWidget;
    let id: string = args.id ?? '';

    // Wait for backend to load/reload plugins.
    await IpylabModel.backend_ready.promise;
    if (IpylabModel.connections.has(cid)) {
      luminoWidget = await IpylabBackendModel.fromConnectionOrId(cid);
    } else if (id) {
      // An existing widget
      ({ luminoWidget, kernelId } = await IpylabModel.toLuminoWidget(
        id,
        kernelId
      ));
    } else if (!(luminoWidget instanceof Widget) && args.evaluate) {
      // Evaluate code in a kernel to create the widget.
      id = await JupyterFrontEndModel.evaluate(args);
      return await JupyterFrontEndModel.addToShell({ ...args, id });
    } else {
      throw new Error('Insufficient info provided to add to the shell');
    }

    cid = cid || `ipylab-shell-connection:${UUID.uuid4()}`;
    area = area || 'main';

    if (
      (area === 'main' && !(luminoWidget instanceof MainAreaWidget)) ||
      typeof luminoWidget.title === 'undefined'
    ) {
      const w = (luminoWidget = new MainAreaWidget({ content: luminoWidget }));
      w.node.removeChild(w.toolbar.node);
      w.addClass('ipylab-MainArea');
    }
    luminoWidget.addClass('ipylab-shell');
    luminoWidget.id = id = id || cid;
    (luminoWidget as any).ipylabSettings = { ...args, id, cid, kernelId };
    IpylabModel.registerConnection(cid, luminoWidget);
    IpylabModel.app.shell.add(luminoWidget as any, area, options);
    if (!IpylabModel.tracker.has(luminoWidget)) {
      if (id && id.slice(0, 10) === 'IPY_MODEL_') {
        // We add ipywidgets so they can be restored, other widgets should have their own tracker.
        IpylabModel.tracker.add(luminoWidget);
        JupyterFrontEndModel.updateTrackers();
        luminoWidget.disposed.connect(() =>
          JupyterFrontEndModel.updateTrackers()
        );
      } else {
        IpylabModel.tracker.inject(luminoWidget);
      }
    }
    return luminoWidget;
  }

  static async updateTrackers() {
    for (const value of IpylabModel.jfemPromises.values()) {
      const jfem: JupyterFrontEndModel = await value.promise;
      jfem.updateTrackerInfo();
    }
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return { ...super.defaults(), _model_name: 'JupyterFrontEndModel' };
  }
}
