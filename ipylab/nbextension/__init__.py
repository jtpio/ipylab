#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jeremy Tuloup
# Distributed under the terms of the Modified BSD License.

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'nbextension/static',
        'dest': 'ipylab',
        'require': 'ipylab/extension'
    }]
