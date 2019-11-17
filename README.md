# ipylab

![Github Actions Status](https://github.com/jtpio/ipylab/workflows/CI/badge.svg)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/jtpio/ipylab/stable?urlpath=lab/tree/examples/introduction.ipynb)

Control JupyterLab from Python notebooks.

The goal is to provide access to most of the JupyterLab environment from Python notebooks. For example:

- Adding widgets to the main area `DockPanel`, left, right or top area
- Build more advanced interfaces leveraging `SplitPanel`, `Toolbar` and other Phosphor widgets
- Launch arbitrary commands (new terminal, change theme, open file and so on)
- Open a workspace with a specific layout
- Listen to JupyterLab signals (notebook opened, console closed) and trigger Python callbacks

## Examples

### Command Registry

![command-registry](./docs/screencasts/commands.gif)

### Widgets and Panels

![widgets-panels](https://user-images.githubusercontent.com/591645/69000410-8f151f00-08cf-11ea-8491-7b8848497b62.gif)

## Installation

You can install using `pip`:

```bash
pip install ipylab
jupyter labextension install @jupyter-widgets/jupyterlab-manager ipylab
```

## Development

```bash
python -m pip install -e .
jlpm && jlpm run build
jupyter labextension install @jupyter-widgets/jupyterlab-manager . --debug
```
