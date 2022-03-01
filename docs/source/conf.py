# -*- coding: utf-8 -*-
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'jupyterlite_sphinx'
]

templates_path = ['_templates']

# jupyterlite_config = "jupyterlite_config.json"

master_doc = 'index'
source_suffix = '.rst'

# General information about the project.
project = 'ipylab'
author = 'ipylab contributors'

exclude_patterns = []
highlight_language = 'python'
pygments_style = 'sphinx'

# Output file base name for HTML help builder.
html_theme = "pydata_sphinx_theme"
htmlhelp_basename = 'ipylabdoc'

html_theme_options = dict(
    github_url='https://github.com/jtpio/ipylab'
)

html_static_path = ['_static']

autodoc_member_order = 'bysource'
