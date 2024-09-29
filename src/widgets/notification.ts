// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.

import { Notification } from '@jupyterlab/apputils';
import { ObservableDisposableDelegate } from '@lumino/disposable';
import { IpylabModel } from './ipylab';
/**
 * The model for a notification.
 */
export class NotificationManagerModel extends IpylabModel {
  async ipylabInit(base: any = null) {
    Notification.manager.changed.connect(this.update, this);
    await super.ipylabInit(base);
  }

  close(comm_closed?: boolean): Promise<void> {
    Notification.manager.changed.disconnect(this.update, this);
    return super.close(comm_closed);
  }

  update() {
    for (const id of this.notifications.keys()) {
      if (!Notification.manager.has(id)) {
        const obj = this.notifications.get(id);
        if (obj) {
          obj.dispose();
        }
        this.notifications.delete(id);
      }
    }
  }

  async operation(op: string, payload: any): Promise<any> {
    switch (op) {
      case 'notification':
        const { message, type, options } = payload;
        const id = Notification.manager.notify(message, type, options);
        const obj = new ObservableDisposableDelegate(() =>
          Notification.manager.dismiss(id)
        ) as any;
        obj.id = id;
        this.notifications.set(id, obj);
        return obj;
      case 'createAction':
        const action = { ...payload } as any;
        action.callback = (event: MouseEvent) => {
          action.keep_open ? event.preventDefault() : null;
          return this.scheduleOperation(
            'action callback',
            { cid: action.cid },
            'done'
          );
        };
        return action;
      default:
        return await super.operation(op, payload);
    }
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: NotificationManagerModel.model_name
    };
  }
  notifications = new Map<string, ObservableDisposableDelegate>();
  static model_name = 'NotificationManagerModel';
}
