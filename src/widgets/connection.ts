// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
import { ObjectHash } from 'backbone';
import { IpylabModel } from './ipylab';

/**
 * Provides a connection from any object reachable here to one or more Python backends.
 *
 * Typically the object is registered first via the method `registerConnection` with a cid
 * In Python The `cid` is passed when creating a new Connection.
 *
 * The object is set as the base. If the object is disposable, the ConnectionModel will
 * also close when the object is disposed.
 */
export class ConnectionModel extends IpylabModel {
  async initialize(attributes: ObjectHash, options: any): Promise<void> {
    await super.initialize(attributes, options);
    this.base.disposed.connect(() => this.close());
    this.on('change:_dispose', this.dispose, this);
  }

  close(comm_closed?: boolean): Promise<void> {
    if (this.base?.ipylabDisposeOnClose) {
      delete this.base.ipylabDisposeOnClose;
      this.dispose();
    }
    return super.close((comm_closed || this.get('_dispose')) ?? false);
  }

  dispose() {
    this.base?.dispose();
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
