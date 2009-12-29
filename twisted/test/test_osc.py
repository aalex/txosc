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

    def testFromBinary(self):
        data = "aaa\0bb\0\0c\0\0\0dddd"
        first, leftover = osc.StringArgument.fromBinary(data) 
        #padding with 0 to make strings length multiples of 4 chars
        self.assertEqual(first.value, "aaa")
        self.assertEqual(leftover, "bb\0\0c\0\0\0dddd")

        second, leftover = osc.StringArgument.fromBinary(leftover)
        self.assertEqual(second.value, "bb")
        self.assertEqual(leftover, "c\0\0\0dddd")

        third, leftover = osc.StringArgument.fromBinary(leftover)
        self.assertEqual(third.value, "c")
        self.assertEqual(leftover, "dddd")

class TestFloatArgument(unittest.TestCase):
    
    def testToAndFromBinary(self):
        binary = osc.FloatArgument(3.14159).toBinary()
        float_arg = osc.FloatArgument.fromBinary(binary)[0] 
        #FIXME: how should we compare floats? use decimal?
        if float_arg.value < 3.1415:
            self.fail("value is too small")
        if float_arg.value > 3.1416:
            self.fail("value is too big")

class TestIntArgument(unittest.TestCase):
    
    def testToAndFromBinary(self):
        binary = osc.IntArgument(12345).toBinary()
        int_arg = osc.IntArgument.fromBinary(binary)[0] 
        self.assertEqual(int_arg.value, 12345)

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

