# ipylab

![Github Actions Status](https://github.com/jtpio/ipylab/workflows/Build/badge.svg)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jtpio/ipylab/stable?urlpath=lab/tree/examples/widgets.ipynb)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/ipylab.svg)](https://anaconda.org/conda-forge/ipylab)
[![pypi](https://img.shields.io/pypi/v/ipylab.svg)](https://pypi.python.org/pypi/ipylab)
[![npm](https://img.shields.io/npm/v/ipylab.svg)](https://www.npmjs.com/package/ipylab)

Control JupyterLab from Python notebooks.

The goal is to provide access to most of the JupyterLab environment from Python notebooks. For example:

- Adding widgets to the main area `DockPanel`, left, right or top area
- Build more advanced interfaces leveraging `SplitPanel`, `Toolbar` and other Lumino widgets
- Launch arbitrary commands (new terminal, change theme, open file and so on)
- Open a workspace with a specific layout
- Listen to JupyterLab signals (notebook opened, console closed) and trigger Python callbacks

## Try it online

Try it in your browser with Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jtpio/ipylab/stable?urlpath=lab/tree/examples/widgets.ipynb)

## Examples

### Add Jupyter Widgets to the JupyterLab interface

![widgets-panels](https://user-images.githubusercontent.com/591645/80025074-59104280-84e0-11ea-9766-0cb49cba285a.gif)

### Execute Commands

![command-registry](https://user-images.githubusercontent.com/591645/80026017-beb0fe80-84e1-11ea-842d-fa3bf5bc4a9b.gif)

### Custom Python Commands and Command Palette

![custom-commands](https://user-images.githubusercontent.com/591645/80026023-c1135880-84e1-11ea-9e83-fdb739659357.gif)

### Build small applications

![ipytree-example](https://user-images.githubusercontent.com/591645/80026006-b8bb1d80-84e1-11ea-87cc-86495186b938.gif)

## Installation

You can install using `pip`:

```bash
pip install ipylab
```

Or with `mamba` / `conda`:

```bash
mamba install -c conda-forge ipylab
```

## Running the examples locally

To try out the examples locally, the recommended way is to create a new environment with the dependencies:

```bash
# create a new conda environment
conda create -n ipylab-examples -c conda-forge jupyterlab ipylab ipytree bqplot ipywidgets numpy
conda activate ipylab-examples

# start JupyterLab
jupyter lab
```

## Under the hood

`ipylab` can be seen as a proxy from Python to JupyterLab over Jupyter Widgets:

![ipylab-diagram](./docs/ipylab.png)

## Development

```bash
# create a new conda environment
mamba create -n ipylab -c conda-forge jupyter-packaging nodejs python -y

# activate the environment
conda activate ipylab

# install the Python package
python -m pip install -e ".[dev]"

# link the extension files
jupyter labextension develop . --overwrite

# compile the extension
jlpm && jlpm run build
```

## Related projects

There are a couple of projects that also enable interacting with the JupyterLab environment from Python notebooks:

- [wxyz](https://github.com/deathbeds/wxyz): experimental widgets (including `DockPanel`)
- [jupyterlab-sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar): add widgets to the JupyterLab right area
- [jupyterlab_commands](https://github.com/timkpaine/jupyterlab_commands): add arbitrary Python commands to the jupyterlab command palette
