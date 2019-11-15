// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  // Add any needed widget imports here (or from controls)
} from '@jupyter-widgets/base';

import {
  createTestModel
} from './utils.spec';

import {
  ShellModel, ShellView
} from '../../src/'


describe('Example', () => {

  describe('ExampleModel', () => {

    it('should be createable', () => {
      let model = createTestModel(ShellModel);
      expect(model).to.be.an(ShellView);
      expect(model.get('value')).to.be('Hello World');
    });

    it('should be createable with a value', () => {
      let state = { value: 'Foo Bar!' }
      let model = createTestModel(ShellModel, state);
      expect(model).to.be.an(ShellModel);
      expect(model.get('value')).to.be('Foo Bar!');
    });

  });

});
