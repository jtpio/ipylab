// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import { ObjectHash } from 'backbone';
import { IpylabModel } from './ipylab';

/**
 * Maintain a connection to any object by using a cid.
 */
export class ConnectionModel extends IpylabModel {
  async initialize(attributes: ObjectHash, options: any): Promise<void> {
    super.initialize(attributes, {
      ...options,
      base: this.getConnection(this.get('cid'))
    });
    this.base.disposed.connect(() => {
      if (!this.get('_dispose')) {
        this.close();
      }
    });
    this.listenTo(this, 'change:_dispose', () => this.base.dispose());
  }

  close(comm_closed?: boolean): Promise<void> {
    if (this.base?.ipylabDisposeOnClose) {
      delete this.base.ipylabDisposeOnClose;
      this.base.dispose();
    }
    return super.close(comm_closed);
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: IpylabModel.connection_model_name,
      _model_module: IpylabModel.model_module,
      _model_module_version: IpylabModel.model_module_version,
      _view_name: null,
      _view_module: null,
      _view_module_version: null
    };
  }
  static model_name = 'ConnectionModel';
  static serializers = {
    ...IpylabModel.serializers,
    content: { deserialize: unpack_models }
  };
}
