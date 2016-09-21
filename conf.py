#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess

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

exclude_patterns = ['.env']

git_describe = subprocess.check_output('git describe --always', shell=True)\
    .decode('utf-8').strip()
version, release = re.match(
    '(?P<version>\d+.\d+).(?P<release>.*)', git_describe).groups()

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
html_show_sourcelink = True

source_suffix = ['.rst', '.md']

source_parsers = {
    '.md': CommonMarkParser,
}


# extra filters

def slug(text):
    """
    >>> slug("com.toptal.platform.Role#user_id")
    'com-toptal-platform-role-user_id'
    """
    return re.sub('[^a-z0-9_]+', '-', text.lower())


def add_jinja_filters(app):
    filters = app.builder.templates.environment.filters

    filters['slug'] = slug


def setup(app):
    app.add_object_type('bqfield', 'bqfield',
                        objname='bigquery field',
                        indextemplate='pair: %s; bigquery field')
    app.connect("builder-inited", add_jinja_filters)
