// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { IBackboneModelOptions, unpack_models } from '@jupyter-widgets/base';
import { ObjectHash } from 'backbone';
import { IpylabModel } from './ipylab';

/**
 * Maintain a connection to a Lumino widget such as a MainAreaWidget, Console, TextEditor, etc...
 * The widget must exist in the shell or have already been added to the tracker.
 *
 */
export class DisposableConnectionModel extends IpylabModel {
  async initialize(
    attributes: ObjectHash,
    options: IBackboneModelOptions
  ): Promise<void> {
    super.initialize(attributes, options);
    this.base.disposed.connect(() => {
      if (!this.get('_dispose')) {
        this.close();
      }
    });
    this.listenTo(this, 'change:_dispose', () => this.base.dispose());
  }

  get base() {
    try {
      return this.getDisposable(this.get('id'));
    } catch {
      this.close();
    }
  }

  /**
   * The default attributes.
   */
  defaults(): Backbone.ObjectHash {
    return {
      ...super.defaults(),
      _model_name: IpylabModel.disposable_model_name,
      _model_module: IpylabModel.model_module,
      _model_module_version: IpylabModel.model_module_version,
      _view_name: null,
      _view_module: null,
      _view_module_version: null
    };
  }
  static model_name = 'DisposableConnectionModel';
  static serializers = {
    ...IpylabModel.serializers,
    content: { deserialize: unpack_models }
  };
}
