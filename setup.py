#!/usr/bin/env python
"""
txosc installation script
"""

from setuptools import setup

__version__ = "0.1"

setup(
    name = "txosc",
    version = __version__,
    author = "Arjan Scherpenisse and Alexandre Quessy",
    author_email = "alexandre@quessy.net",
    url = "http://bitbucket.org/arjan/twisted-osc",
    description = "Open Sound Control Protocol for Twisted",
    install_requires = [], # twisted
    scripts = [],
    packages = ["txosc", "txosc/test"]
    )

