#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os

from glob import glob
from os.path import join as pjoin

from jupyter_packaging import (
    create_cmdclass,
    install_npm,
    ensure_targets,
    combine_commands,
    ensure_python,
    get_version,
    skip_if_exists,
)

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


# The name of the project
name = "ipylab"

# Ensure a valid python version
ensure_python(">=3.6")

# Get our version
version = get_version(pjoin(name, "_version.py"))

lab_path = pjoin(HERE, name, "labextension")

# Representative files that should exist after a successful build
jstargets = [
    pjoin(HERE, "lib", "plugin.js"),
]

package_data_spec = {name: ["labextension/*"]}

labext_name = "ipylab"

data_files_spec = [
    ("share/jupyter/labextensions/%s" % labext_name, lab_path, "**"),
]

js_command = combine_commands(
    install_npm(HERE, build_cmd="build:prod", npm=["jlpm"]),
    ensure_targets(jstargets),
)

cmdclass = create_cmdclass(
    "jsdeps", package_data_spec=package_data_spec, data_files_spec=data_files_spec
)

is_repo = os.path.exists(os.path.join(HERE, ".git"))
if is_repo:
    cmdclass["jsdeps"] = js_command
else:
    cmdclass["jsdeps"] = skip_if_exists(jstargets, js_command)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = dict(
    name=name,
    version=version,
    description="Control JupyterLab from Python Notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    cmdclass=cmdclass,
    packages=find_packages(),
    author="ipylab contributors",
    author_email="jeremy@jtp.io",
    url="https://github.com/jtpio/ipylab",
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "Widgets", "IPython"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Framework :: Jupyter",
    ],
    include_package_data=True,
    install_requires=["ipywidgets>=7.6.0", "jupyterlab~=3.0"],
    extras_require={
        "test": [
            "pytest>=3.6",
            "pytest-cov",
            "nbval",
        ],
        "dev": ["pre-commit", "black"],
        "examples": [
            # Any requirements for the examples to run
        ],
        "docs": [
            "sphinx>=1.5",
            "recommonmark",
            "sphinx_rtd_theme",
            "nbsphinx>=0.2.13,<0.4.0",
            "jupyter_sphinx",
            "nbsphinx-link",
            "pytest_check_links",
            "pypandoc",
        ],
    },
    entry_points={},
)

if __name__ == "__main__":
    setup(**setup_args)
