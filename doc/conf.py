# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "shardproxy"
copyright = ""
author = ""
release = ""

extensions = ["sphinx.ext.autodoc", "sphinx.ext.intersphinx", "sphinx.ext.napoleon"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
add_module_names = False
# autodoc_type_aliases = {'ResultRows': 'ResultRows'}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20", None),
}

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"

html_theme_options = {"show_powered_by": "false"}
# html_static_path = ["_static"]
html_domain_indices = False
html_use_index = True
html_split_index = False
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = False
