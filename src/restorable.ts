import { Widget } from '@phosphor/widgets';

export class RestorableWidget extends Widget {
  /**
   * Instantiate a new RestorableWidget.
   * @param options The instantiation options for a Restorable Widget.
   */
  constructor(options: RestorableWidget.IOptions) {
    super();
    const { modelId } = options;
    console.log(modelId);
  }
}

/**
 * A namespace for RestorableWidget `statics`
 */
export namespace RestorableWidget {
  /**
   * Instantiation options for a RestorableWidget
   */
  export interface IOptions {
    /**
     * The model id of the widget to restore.
     */
    modelId: string;
  }
}
