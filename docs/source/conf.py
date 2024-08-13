# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "stem_mixer"
copyright = "2024, Giovana Morais and Lindsey Pietrewicz"
author = "Giovana Morais and Lindsey Pietrewicz"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import sys

extensions = [
    "sphinx.ext.autodoc", # function indexing
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode", # get function source
]

templates_path = ["_templates"]
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
