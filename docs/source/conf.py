# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import pathlib, sys
sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())

project = 'Ground Station Documentation'
copyright = '2024, ground station subteam'
author = 'ground station subteam'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.doctest', 'sphinx.ext.autodoc', 'sphinx.ext.autosummary']
source_dir = "docs/source"
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "groundwork"
html_static_path = ['_static']
html_css_files = ['custom.css']
