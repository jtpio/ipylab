# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

import pluggy

import ipylab.hookspecs, ipylab.lib

pm = pluggy.PluginManager("ipylab")
pm.add_hookspecs(ipylab.hookspecs)
pm.load_setuptools_entrypoints("ipylab-python-backend")
pm.register(ipylab.lib)
