# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import django

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Django Channel Tasks'
copyright = '2024, Daniel Farré Manzorro'
author = 'Daniel Farré Manzorro'
release = '0.9'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []
extensions = [
    'sphinx.ext.autodoc',
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
html_theme_options = {
    'sidebarwidth': '25%',
    'body_min_width': '95%',
}
html_static_path = ['_static']

# -- Initialization ----------------------------------------------------------
# A Django setup is required to auto-doc Django app modules
django.setup()
