// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { unpack_models } from '@jupyter-widgets/base';
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
  async ipylabInit(base: any = null) {
    this.on('change:_dispose', this.dispose, this);
    await IpylabModel.tracker.restored;
    const cid = this.get('cid');
    const id = this.get('id') ?? '';
    try {
      base = await IpylabModel.fromConnectionOrId(cid, id);
    } catch {
      console.log('Connection not found for cid="%s" id="%s "', cid, id);
    }
    IpylabModel.registerConnection(cid, base);
    base.disposed.connect(() => this.close());
    await super.ipylabInit(base);
  }

  get base() {
    const base = IpylabModel.connections.get(this.get('cid'));
    if (typeof base === 'undefined') {
      this.close();
    }
    return base;
  }

  get isConnectionModel() {
    return true;
  }

  close(comm_closed?: boolean): Promise<void> {
    if ((this.base as any)?.ipylabDisposeOnClose) {
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
