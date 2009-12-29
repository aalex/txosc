# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
OSC tests.

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest
from twisted.protocols import osc

class TestStringArgument(unittest.TestCase):
    """
    Encoding and decoding of a string argument.
    """
    def testToBinary(self):
        self.assertEqual(osc.StringArgument("").toBinary(), "\0\0\0\0")
        self.assertEqual(osc.StringArgument("OSC").toBinary(), "OSC\0")
        self.assertEqual(osc.StringArgument("Hello").toBinary(), "Hello\0\0\0")


class TestServer(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    pass

class TestParsing(unittest.TestCase):
    def testStringParsing(self):
        pass
        first_string, leftover = osc._readString("/hello\0s\0spam")
        self.assertEqual(first_string, "/hello")
        self.assertEqual(leftover, "s\0spam")
        second_string, leftover = osc._readString(leftover)
        self.assertEqual(second_string, "s")
        self.assertEqual(leftover, "spam")
        third_string, leftover = osc._readString(leftover)
        self.assertEqual(third_string, "spam")
        self.assertEqual(leftover, "")
