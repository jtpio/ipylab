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

### Widgets and Panels

![widgets-panels](https://user-images.githubusercontent.com/591645/69000410-8f151f00-08cf-11ea-8491-7b8848497b62.gif)

### Command Registry

![command-registry](./docs/screencasts/commands.gif)

### Custom Python Commands and Command Palette

![custom-commands](https://user-images.githubusercontent.com/591645/73125753-adbc2400-3faa-11ea-95f8-f7060e883ccd.gif)

## Installation

You can install using `pip`:

```bash
pip install ipylab
```

Or with `conda`:

```bash
conda install -c conda-forge ipylab
```

To install the JupyterLab extension:

```bash
jupyter labextension install @jupyter-widgets/jupyterlab-manager ipylab
```

## Development

```bash
python -m pip install -e ".[dev]"
jlpm && jlpm run build
jupyter labextension install @jupyter-widgets/jupyterlab-manager . --debug
```

## Related projects

There are a couple of projects that also enable interacting with the JupyterLab environment from Python notebooks:

- [wxyz](https://github.com/deathbeds/wxyz): experimental widgets (including `DockPanel`)
- [jupyterlab-sidecar](https://github.com/jupyter-widgets/jupyterlab-sidecar): add widgets to the JupyterLab right area
- [jupyterlab_commands](https://github.com/timkpaine/jupyterlab_commands): add arbitrary Python commands to the jupyterlab command palette
