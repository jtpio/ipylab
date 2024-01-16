// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { ISerializers } from '@jupyter-widgets/base';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { IpylabModel } from './ipylab';

/**
 * The model for a JupyterFrontEnd.
 */
export class JupyterFrontEndModel extends IpylabModel {
  /**
   * The default attributes.
   */
  defaults(): any {
    return {
      ...super.defaults(),
      _model_name: JupyterFrontEndModel.model_name,
      _model_module: JupyterFrontEndModel.model_module,
      _model_module_version: JupyterFrontEndModel.model_module_version
    };
  }

  /**
   * Initialize a JupyterFrontEndModel instance.
   *
   * @param attributes The base attributes.
   * @param options The initialization options.
   */
  initialize(attributes: any, options: any): void {
    this._app = JupyterFrontEndModel.app;
    super.initialize(attributes, options);
    this.set('version', this._app.version);
    // const msg = 'ipylab_' + JupyterFrontEndModel.model_name + '_ready';
    // this.send({ event: msg }, {});
    this.save_changes();
  }

  static serializers: ISerializers = {
    ...IpylabModel.serializers
  };

  static model_name = 'JupyterFrontEndModel';

  private _app!: JupyterFrontEnd;
  static app: JupyterFrontEnd;
}
