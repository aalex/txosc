#!/usr/bin/env python
"""
txosc installation script
"""
import sys
import subprocess
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

if sys.argv[1] == "build":
    commands = [
        'help2man --no-info --include=man-osc-send.txt --name="sends an OSC message" ./scripts/osc-send --output=osc-send.1',
        'help2man --no-info --include=man-osc-receive.txt --name="receives OSC messages" ./scripts/osc-receive --output=osc-receive.1',
        ]
    for c in commands:
        print("$ %s" % (c))
        retcode = subprocess.call(c, shell=True)
        print("The help2man command returned %s" % (retcode))

