// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { IpylabModel, IObservableDisposable } from './ipylab';

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
  async ipylabInit() {
    this.on('change:_dispose', this.disposeBase, this);
    await IpylabModel.tracker.restored;
    const cid = this.get('cid');
    const id = this.get('id') ?? '';
    try {
      const base = await IpylabModel.fromConnectionOrId(cid, id);
      IpylabModel.registerConnection(cid, base);
      this.base;
    } catch {
      console.log('Connection not found for cid="%s" id="%s "', cid, id);
    }
    await super.ipylabInit();
  }

  get base() {
    const base = IpylabModel.connections.get(this.get('cid'));
    if (typeof base === 'undefined') {
      // Trigger close if not already disposed.
      this.close(!Boolean(this.comm), true);
    }
    if (base !== this.currentbase) {
      this.currentbase?.disposed?.disconnect(this.onBaseDisposed, this);
      this.currentbase = base;
      this.currentbase?.disposed?.connect(this.onBaseDisposed, this);
    }
    return base;
  }

  onBaseDisposed() {
    this.close(null, true);
  }

  close(comm_closed?: boolean, base_closed?: boolean): Promise<void> {
    if (!base_closed && (this.base as any)?.ipylabDisposeOnClose) {
      this.disposeBase();
    }
    return super.close((comm_closed || this.get('_dispose')) ?? false);
  }

  disposeBase() {
    this.base?.dispose();
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return { ...super.defaults(), _model_name: 'ConnectionModel' };
  }
  readonly isConnectionModel = true;
  private currentbase: IObservableDisposable;
  static model_name = 'ConnectionModel';
}
