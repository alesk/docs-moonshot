# Teftel-Docs MoonShot

This document is authored with Markdown to demonstrate the usage
of markdown markup language as an addition to restructured text.

![moon shot](http://www.theallium.com/wp-content/uploads/2016/02/Moonshot.jpg)

## Install

On windows, do:

```
python -m venv .enw
.enw\Scripts\activate.bat
pip install -r requirements.txt
```

on linux/MacOs

```
python -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

## Run

Make sure to activate virtualenv.

Use `make` to build documentation.
Use `python -m http.server` in `_build/html` to serve documentation.

## Motivation

It's hard to do too many things at a time, so this repository is
about reherasing [restructured text][1] and [sphinx][2].


[1]: http://docutils.sourceforge.net/docs/user/rst/quickref.html
[2]: http://www.sphinx-doc.org/en/stable/
