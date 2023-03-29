extensions = ["myst_parser", "jupyterlite_sphinx"]

jupyterlite_config = "jupyter_lite_config.json"
jupyterlite_dir = "."
jupyterlite_contents = "../examples"

master_doc = "index"
source_suffix = ".md"

# General information about the project.
project = "ipylab"
author = "ipylab contributors"

exclude_patterns = []
highlight_language = "python"
pygments_style = "sphinx"

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]

html_css_files = ["custom.css"]
