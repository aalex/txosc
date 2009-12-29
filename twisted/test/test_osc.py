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


class TestMessage(unittest.TestCase):
    def testGetTypeTag(self):
        m = osc.Message("/example")
        self.assertEqual(m.getTypeTags(), "")
        m.arguments.append(osc.StringArgument("egg"))
        self.assertEqual(m.getTypeTags(), "s")
        m.arguments.append(osc.StringArgument("spam"))
        self.assertEqual(m.getTypeTags(), "ss")
        

class TestServer(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    pass

class TestParsing(unittest.TestCase):
    def testStringParsing(self):
        first_string, leftover = osc._readString("aaa\0bb\0\0c\0\0\0dddd") 
        #padding with 0 to make strings length multiples of 4 chars
        self.assertEqual(first_string, "aaa")
        self.assertEqual(leftover, "bb\0\0c\0\0\0dddd")
        
        second_string, leftover = osc._readString(leftover)
        self.assertEqual(second_string, "bb")
        self.assertEqual(leftover, "c\0\0\0dddd")
        
        third_string, leftover = osc._readString(leftover)
        #print("\n 3rd %s leftover: %s" % (third_string, leftover))
        self.assertEqual(third_string, "c")
        self.assertEqual(leftover, "dddd")
