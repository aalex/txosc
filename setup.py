#!/usr/bin/env python
"""
txosc installation script
"""
from setuptools import setup
import os
import sys
import subprocess
import txosc
from twisted.python import procutils

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
    if os.path.exists("man-osc-send.txt"):
        try:
            help2man = procutils.which("help2man")[0]
        except IndexError:
            print("Cannot build the man pages. help2man was not found.")
        else:
            for c in commands:
                print("$ %s" % (c))
                retcode = subprocess.call(c, shell=True)
                print("The help2man command returned %s" % (retcode))

