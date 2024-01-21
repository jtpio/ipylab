# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.


import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ipylab-backend":
        from ipylab.scripts import init_ipylab_backend

        init_ipylab_backend()
    else:
        if not sys.argv:
            sys.argv = ["--ServerApp.token=''"]
        from ipylab.scripts import launch_jupyterlab

        launch_jupyterlab()
