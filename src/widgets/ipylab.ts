// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

// SessionManager exposes `JupyterLab.serviceManager.sessions` to user python kernel

import {
  IBackboneModelOptions,
  ISerializers,
  WidgetModel
} from '@jupyter-widgets/base';

import { JSONValue } from '@lumino/coreutils';

import { ObjectHash } from 'backbone';

import { MODULE_NAME, MODULE_VERSION } from '../version';

import { ILabShell, JupyterFrontEnd, LabShell } from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { IDefaultFileBrowser } from '@jupyterlab/filebrowser';

import { CommandRegistry } from '@lumino/commands';

export {
  CommandRegistry,
  IBackboneModelOptions,
  ILabShell,
  ISerializers,
  JSONValue,
  JupyterFrontEnd
};

/**
 * Base model for common features
 */
export class IpylabModel extends WidgetModel {
  initialize(attributes: ObjectHash, options: IBackboneModelOptions): void {
    super.initialize(attributes, options);
    this.on('msg:custom', this._onCustomMessage.bind(this));
    const msg = `ipylab ${this.get('_model_name')} ready for operations`;
    this.send({ init: msg });
    this.on('comm_live_update', () => {
      if (!this.comm_live && this.comm) this.close();
    });
  }
  /**
   * Convert custom messages into events for action with  async operation.
   * @param msg
   */
  private async _onCustomMessage(msg: any): Promise<void> {
    const operation: string = msg.operation;
    const ipylab_ID: string = msg.ipylab_ID;

    if (!operation) {
      throw new Error(`operation not provided`);
    }
    if (!ipylab_ID) {
      throw new Error(`ipylab_ID not provided}`);
    }
    try {
      if (typeof operation != 'string')
        throw new Error(
          `operation must be a string not ${typeof operation}  operation='${operation}'`
        );

      const payload: JSONValue = await this.operation(operation, msg.kwgs);
      if (payload === undefined)
        throw new Error(
          `ipylab ${this.get(
            '_model_name'
          )} bug: operation=${operation} did not return a payload!`
        );
      const content = {
        event: operation,
        ipylab_ID: ipylab_ID,
        payload: payload
      };
      this.send(content);
    } catch (e) {
      const content = {
        event: operation,
        ipylab_ID: msg.ipylab_ID,
        error: String(e)
      };
      this.send(content);
      console.error(e);
    }
  }

  async operation(op: string, payload: any): Promise<JSONValue> {
    // Provide any json content
    switch (op) {
      default:
        throw new Error(
          `operation='${op}' has not been implemented in ${this.get(
            '_model_name'
          )}!`
        );
    }
  }

  static serializers: ISerializers = {
    ...WidgetModel.serializers
  };

  static model_name: string;
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name: string;
  static view_module: string;
  static view_module_version = MODULE_VERSION;

  static app: JupyterFrontEnd;
  static shell: JupyterFrontEnd.IShell;
  static labShell: LabShell;
  static defaultBrowser: IDefaultFileBrowser;
  static palette: ICommandPalette;
  static commands: CommandRegistry;
}
