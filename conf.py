#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os.path
import re
import subprocess
import recommonmark
import sphinx_rtd_theme
from recommonmark.parser import CommonMarkParser

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode'
]

templates_path = ['_templates']

master_doc = 'index'

project = 'Teftel'
copyright = '2016, Toptal Analytics Team'
author = 'Toptal Analytics Team'

git_describe = subprocess.check_output('git describe --always', shell=True).decode('utf-8').strip()
version, release = re.match('(?P<version>\d+.\d+).(?P<release>.*)', git_describe).groups()

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
html_show_sourcelink = True


source_suffix = ['.rst', '.md']

source_parsers = {
    '.md': CommonMarkParser,
}
