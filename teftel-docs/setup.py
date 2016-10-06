from setuptools import setup, find_packages

setup(
      name='teftel_docs',
      version='0.1.0',
      description='Teftel schemata documentation',
      url='http://github.com/toptal/teftel',
      license='Proprietary',
      packages=find_packages(),
      scripts=['bin/schema-to-rst.py'],
      install_requires=[
            'jinja2==2.8',
            'Sphinx==1.4.6',
            'sphinx_rtd_theme==0.1.9',
            'recommonmark==0.4.0'
      ]
)
