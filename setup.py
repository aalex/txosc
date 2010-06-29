#!/usr/bin/env python
"""
txosc installation script
"""

from setuptools import setup
import txosc

setup(
    name = "txosc",
    version = txosc.__version__,
    author = "Arjan Scherpenisse and Alexandre Quessy",
    author_email = "txosc@toonloop.com",
    url = "http://bitbucket.org/arjan/txosc",
    description = "Open Sound Control Protocol for Twisted",
    scripts = [
        "scripts/osc-receive", 
        "scripts/osc-send"
        ],
    license="MIT/X",
    packages = ["txosc", "txosc/test"],
    long_description = """Open Sound Control (OSC) is an open, transport-independent, message-based protocol developed for communication among computers, sound synthesizers, and other multimedia devices. 

This library implements OSC version 1.1 over both UDP and TCP for the Twisted Python framework. 
  """,
    classifiers = [
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Communications",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
        ]
    )

