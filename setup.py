#!/usr/bin/env python
"""
txosc installation script
"""

from setuptools import setup

__version__ = "0.1.2"

setup(
    name = "txosc",
    version = __version__,
    author = "Arjan Scherpenisse and Alexandre Quessy",
    author_email = "txosc@toonloop.com",
    url = "http://bitbucket.org/arjan/txosc",
    description = "Open Sound Control Protocol for Twisted",
    #install_requires = ["twisted"],
    scripts = [],
    license="MIT/X",
    packages = ["txosc", "txosc/test"],
    long_description = """Open Sound Control (OSC) is an open, transport-independent, message-based protocol developed for communication among computers, sound synthesizers, and other multimedia devices. 

This library implements OSC version 1.1 over both UDP and TCP for the Twisted Python framework. 
  """
    )

