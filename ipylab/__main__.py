# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.


import sys

if __name__ == "__main__":
    if not sys.argv:
        sys.argv = ["--ServerApp.token=''"]
    from ipylab.scripts import launch_jupyterlab

    launch_jupyterlab()
