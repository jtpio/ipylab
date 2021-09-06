#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from pathlib import Path

import setuptools

HERE = Path(__file__).parent.resolve()

# The name of the project
NAME = "ipylab"

lab_path = HERE / NAME / "labextension"

# Representative files that should exist after a successful build
ensured_targets = [str(lab_path / "static" / "style.js")]

data_files_spec = [
    ("share/jupyter/labextensions/%s" % NAME, str(lab_path), "**"),
    ("share/jupyter/labextensions/%s" % NAME, str(HERE), "install.json"),
]

try:
    from jupyter_packaging import wrap_installers, npm_builder, get_data_files

    # In develop mode, just run yarn
    builder = npm_builder(build_cmd="build", npm="jlpm", force=True)
    cmdclass = wrap_installers(post_develop=builder, ensured_targets=ensured_targets)

    setup_args = dict(cmdclass=cmdclass, data_files=get_data_files(data_files_spec))
except ImportError:
    setup_args = dict()


if __name__ == "__main__":
    setuptools.setup(**setup_args)
