import os
import sys
sys.path.insert(0, os.path.abspath('../src/e3v3se_display'))


project = 'E3V3SE_display_klipper'
copyright = '2024, Joao Curti'
author = 'Joao Curti'
release = '0.1'


extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.viewcode',
              'myst_parser',]

exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
