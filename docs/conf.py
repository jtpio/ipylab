extensions = ["myst_parser", "jupyterlite_sphinx"]

jupyterlite_config = "jupyter_lite_config.json"
jupyterlite_dir = "."
jupyterlite_contents = "content"

master_doc = "index"
source_suffix = ".md"

# General information about the project.
project = "ipylab"
author = "Jeremy Tuloup"

exclude_patterns = []
highlight_language = "python"
pygments_style = "sphinx"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_css_files = ["custom.css"]


def on_config_inited(*args):
    import sys
    import subprocess
    from pathlib import Path

    HERE = Path(__file__)
    ROOT = HERE.parent.parent
    subprocess.check_call(["jlpm"], cwd=str(ROOT))
    subprocess.check_call(["jlpm", "build"], cwd=str(ROOT))

    subprocess.check_call([sys.executable, "-m", "build"], cwd=str(ROOT))


def setup(app):
    app.connect("config-inited", on_config_inited)
