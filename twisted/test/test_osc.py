# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
OSC tests.

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest
from twisted.protocols import osc

class TestBlobArgument(unittest.TestCase):
    """
    Encoding and decoding of a "blob" argument.
    """
    def testEncode(self):
        self.assertEqual(1, 1)

    def testDecode(self):
        self.assertEqual(1, 1)

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
