# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
Tests for txosc/osc.py

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest
from twisted.internet import reactor, defer, task
from txosc import osc
from txosc import async
from txosc import dispatch

class TestGetAddressParts(unittest.TestCase):
    """
    Test the getAddressParts function.
    """
    def testGetAddressParts(self):
        addresses = {
            "/foo": ["foo"],
            "/foo/bar": ["foo", "bar"],
            "/foo/bar/ham": ["foo", "bar", "ham"],
            "/egg/[1-2]": ["egg", "[1-2]"],
            "/egg/*": ["egg", "*"],
            "/egg/?": ["egg", "?"],
            }
        for k, v in addresses.iteritems():
            self.failUnlessEqual(osc.getAddressParts(k), v)


class TestArgumentCreation(unittest.TestCase):
    """
    Test the L{osc.CreateArgument} function.
    """
    
    def testCreateFromValue(self):
        self.assertEquals(type(osc.createArgument(True)), osc.BooleanArgument)
        self.assertEquals(type(osc.createArgument(False)), osc.BooleanArgument)
        self.assertEquals(type(osc.createArgument(None)), osc.NullArgument)
        self.assertEquals(type(osc.createArgument(123)), osc.IntArgument)
        self.assertEquals(type(osc.createArgument(3.14156)), osc.FloatArgument)
        # Unicode is not supported.
        self.assertRaises(osc.OscError, osc.createArgument, u'test')

    def testCreateFromTypeTag(self):
        self.assertEquals(type(osc.createArgument(123, "T")), osc.BooleanArgument)
        self.assertEquals(type(osc.createArgument(123, "F")), osc.BooleanArgument)
        self.assertEquals(type(osc.createArgument(123, "N")), osc.NullArgument)
        self.assertEquals(type(osc.createArgument(123, "I")), osc.ImpulseArgument)
        self.assertEquals(type(osc.createArgument(123, "i")), osc.IntArgument)
        self.assertEquals(type(osc.createArgument(123, "f")), osc.FloatArgument)
        self.assertRaises(osc.OscError, osc.createArgument, 123, "?")



class TestArgument(unittest.TestCase):
    """
    Encoding and decoding of a string argument.
    """
    def testAbstractArgument(self):
        a = osc.Argument(None)
        self.assertRaises(NotImplementedError, a.toBinary)
        self.assertRaises(NotImplementedError, a.fromBinary, "")


class TestBlobArgument(unittest.TestCase):
    """
    Encoding and decoding of a string argument.
    """
    def testToBinary(self):
        self.assertEquals(osc.BlobArgument("").toBinary(), "\0\0\0\0\0\0\0\0")
        self.assertEquals(osc.BlobArgument("a").toBinary(), "\0\0\0\1a\0\0\0")
        self.assertEquals(osc.BlobArgument("hi").toBinary(), "\0\0\0\2hi\0\0")
        self.assertEquals(osc.BlobArgument("hello").toBinary(), "\0\0\0\5hello\0\0\0")

    def testFromBinary(self):
        data = "\0\0\0\2hi\0\0\0\0\0\5hello\0\0\0"
        first, leftover = osc.BlobArgument.fromBinary(data)
        self.assertEquals(first.value, "hi")
        self.assertEquals(leftover, "\0\0\0\5hello\0\0\0")

        second, leftover = osc.BlobArgument.fromBinary(leftover)
        self.assertEquals(second.value, "hello")
        self.assertEquals(leftover, "")

        # invalid formatted 
        self.assertRaises(osc.OscError, osc.BlobArgument.fromBinary, "\0\0\0") # invalid length packet
        self.assertRaises(osc.OscError, osc.BlobArgument.fromBinary, "\0\0\0\99")


class TestStringArgument(unittest.TestCase):
    """
    Encoding and decoding of a string argument.
    """
    def testToBinary(self):
        self.assertEquals(osc.StringArgument("").toBinary(), "\0\0\0\0")
        self.assertEquals(osc.StringArgument("OSC").toBinary(), "OSC\0")
        self.assertEquals(osc.StringArgument("Hello").toBinary(), "Hello\0\0\0")

    def testFromBinary(self):
        data = "aaa\0bb\0\0c\0\0\0dddd"
        first, leftover = osc.StringArgument.fromBinary(data)
        #padding with 0 to make strings length multiples of 4 chars
        self.assertEquals(first.value, "aaa")
        self.assertEquals(leftover, "bb\0\0c\0\0\0dddd")

        second, leftover = osc.StringArgument.fromBinary(leftover)
        self.assertEquals(second.value, "bb")
        self.assertEquals(leftover, "c\0\0\0dddd")

        third, leftover = osc.StringArgument.fromBinary(leftover)
        self.assertEquals(third.value, "c")
        self.assertEquals(leftover, "dddd")

class TestFloatArgument(unittest.TestCase):

    def testToAndFromBinary(self):
        binary = osc.FloatArgument(3.14159).toBinary()
        float_arg = osc.FloatArgument.fromBinary(binary)[0]
        #FIXME: how should we compare floats? use decimal?
        if float_arg.value < 3.1415:
            self.fail("value is too small")
        if float_arg.value > 3.1416:
            self.fail("value is too big")
        self.assertRaises(osc.OscError, osc.FloatArgument.fromBinary, "\0\0\0") # invalid value

    def testCasting(self):
        # we should be able to cast the argument to float to get its float value
        value = 3.14159
        float_arg = osc.FloatArgument(value)
        if float(float_arg) < 3.1415:
            self.fail("value is too small")
        if float(float_arg) > 3.1416:
            self.fail("value is too big")

class TestIntArgument(unittest.TestCase):

    def testToAndFromBinary(self):
        def test(value):
            int_arg = osc.IntArgument.fromBinary(osc.IntArgument(value).toBinary())[0]
            self.assertEquals(int_arg.value, value)
        test(0)
        test(1)
        test(-1)
        test(1<<31-1)
        test(-1<<31)        
        self.assertRaises(osc.OscError, osc.IntArgument.fromBinary, "\0\0\0") # invalid value

    def testIntOverflow(self):
        self.assertRaises(OverflowError, osc.IntArgument(1<<31).toBinary)
        self.assertRaises(OverflowError, osc.IntArgument((-1<<31) - 1).toBinary)


class TestColorArgument(unittest.TestCase):

    def testToAndFromBinary(self):
        def _test(value):
            color_arg = osc.ColorArgument.fromBinary(osc.ColorArgument(value).toBinary())[0]
            self.assertEquals(color_arg.value, value)
        _test((255, 255, 255, 255))
        _test((0, 0, 0, 0))
        self.assertRaises(osc.OscError, osc.ColorArgument.fromBinary, "\0\0\0") # invalid value
        self.assertRaises(TypeError, osc.ColorArgument.toBinary, (-244, 0, 0, 0)) # invalid value
        self.assertRaises(TypeError, osc.ColorArgument.toBinary, ()) # invalid value



class TestTimeTagArgument(unittest.TestCase):
    def testToBinary(self):
        # 1 second since Jan 1, 1900
        arg = osc.TimeTagArgument(1)
        binary = arg.toBinary()
        self.assertEquals(binary, "\0\0\0\1\0\0\0\0")

    def testFromBinary(self):
        # 1 second since Jan 1, 1900
        self.assertEquals(1.0, osc.TimeTagArgument.fromBinary("\0\0\0\1\0\0\0\0")[0].value)
        # immediately
        self.assertEquals(True, osc.TimeTagArgument.fromBinary("\0\0\0\0\0\0\0\1")[0].value)
        # error
        self.assertRaises(osc.OscError, osc.TimeTagArgument.fromBinary, "\0\0\0\0\0\0")


    def testToAndFromBinary(self):
        # 1 second since Jan 1, 1900
        def test(value):
            timetag_arg, leftover = osc.TimeTagArgument.fromBinary(osc.TimeTagArgument(value).toBinary())
            self.assertEquals(leftover, "")
            self.assertTrue(abs(timetag_arg.value - value) < 1e-6)

        test(1.0)
        test(1.1331)



class TestMessage(unittest.TestCase):

    def testMessageStringRepresentation(self):

        self.assertEquals("/hello", str(osc.Message("/hello")))
        self.assertEquals("/hello ,i i:1 ", str(osc.Message("/hello", 1)))
        self.assertEquals("/hello ,T T:True ", str(osc.Message("/hello", True)))


    def testAddMessageArguments(self):
        """
        Test adding arguments to a message
        """
        m = osc.Message("/example", osc.IntArgument(33), osc.BooleanArgument(True))
        self.assertEquals(m.arguments[0].value, 33)
        self.assertEquals(m.arguments[1].value, True)

        m = osc.Message("/example", 33, True)
        self.assertEquals(m.arguments[0].value, 33)
        self.assertEquals(m.arguments[1].value, True)

        m = osc.Message("/example")
        m.add(33)
        self.assertEquals(m.arguments[0].value, 33)
        self.assertEquals(m.arguments[0].typeTag, "i")
        m.add(True)
        self.assertEquals(m.arguments[1].typeTag, "T")


    def testEquality(self):
        self.assertEquals(osc.Message("/example"),
                         osc.Message("/example"))
        self.assertNotEqual(osc.Message("/example"),
                            osc.Message("/example2"))
        self.assertEquals(osc.Message("/example", 33),
                         osc.Message("/example", 33))
        self.assertNotEqual(osc.Message("/example", 33),
                            osc.Message("/example", 34))
        self.assertNotEqual(osc.Message("/example", 33),
                            osc.Message("/example", 33.0))
        self.assertNotEqual(osc.Message("/example", 33),
                            osc.Message("/example", 33, True))
        self.assertEquals(osc.Message("/example", 33, True),
                         osc.Message("/example", 33, True))



    def testGetTypeTag(self):
        m = osc.Message("/example")
        self.assertEquals(m.getTypeTags(), "")
        m.arguments.append(osc.StringArgument("egg"))
        self.assertEquals(m.getTypeTags(), "s")
        m.arguments.append(osc.StringArgument("spam"))
        self.assertEquals(m.getTypeTags(), "ss")


    def testToAndFromBinary(self):

        self.assertRaises(osc.OscError, osc.Message.fromBinary, "invalidbinarydata..")
        self.assertRaises(osc.OscError, osc.Message.fromBinary, "/example,invalidbinarydata..")
        self.assertRaises(osc.OscError, osc.Message.fromBinary, "/hello\0\0,xxx\0")

        def test(m):
            binary = m.toBinary()
            m2, leftover = osc.Message.fromBinary(binary)
            self.assertEquals(leftover, "")
            self.assertEquals(m, m2)

        test(osc.Message("/example"))
        test(osc.Message("/example", osc.StringArgument("hello")))
        test(osc.Message("/example", osc.IntArgument(1), osc.IntArgument(2), osc.IntArgument(-1)))
        test(osc.Message("/example", osc.BooleanArgument(True)))
        test(osc.Message("/example", osc.BooleanArgument(False), osc.NullArgument(), osc.StringArgument("hello")))
        test(osc.Message("/example", osc.ImpulseArgument()))

    def testGetValues(self):
        # tests calling txosc.osc.Message.getValues()
        
        message = osc.Message("/foo", 2, True, 3.14159)
        values = message.getValues()
        self.failUnlessEqual(values[0], 2)
        self.failUnlessEqual(values[1], True)
        self.failUnlessEqual(values[2], 3.14159)



class TestBundle(unittest.TestCase):

    def testEquality(self):

        self.assertEquals(osc.Bundle(), osc.Bundle())
        self.assertNotEqual(osc.Bundle([osc.Message("/hello")]),
                            osc.Bundle())
        self.assertEquals(osc.Bundle([osc.Message("/hello")]),
                         osc.Bundle([osc.Message("/hello")]))
        self.assertNotEqual(osc.Bundle([osc.Message("/hello")]),
                            osc.Bundle([osc.Message("/hello2")]))


    def testToAndFromBinary(self):

        self.assertRaises(osc.OscError, osc.Bundle.fromBinary, "invalidbinarydata..")
        self.assertRaises(osc.OscError, osc.Bundle.fromBinary, "#bundle|invalidbinarydata..")
        self.assertRaises(osc.OscError, osc.Bundle.fromBinary, "#bundle\0\0\0\0\1\0\0\0\0hello")
        self.assertRaises(osc.OscError, osc.Bundle.fromBinary, "#bundle\0\0\0\0\1\0\0\0\0\0\0\0\5hellofdsfds")

        def test(b):
            binary = b.toBinary()
            b2, leftover = osc.Bundle.fromBinary(binary)
            self.assertEquals(leftover, "")
            self.assertEquals(b, b2)

        test(osc.Bundle())
        test(osc.Bundle([osc.Message("/foo")]))
        test(osc.Bundle([osc.Message("/foo"), osc.Message("/bar")]))
        test(osc.Bundle([osc.Message("/foo"), osc.Message("/bar", osc.StringArgument("hello"))]))

        nested = osc.Bundle([osc.Message("/hello")])
        test(osc.Bundle([nested, osc.Message("/foo")]))

    def testGetMessages(self):

        m1 = osc.Message("/foo")
        m2 = osc.Message("/bar")
        m3 = osc.Message("/foo/baz")

        b = osc.Bundle()
        b.add(m1)
        self.assertEquals(b.getMessages(), set([m1]))

        b = osc.Bundle()
        b.add(m1)
        b.add(m2)
        self.assertEquals(b.getMessages(), set([m1, m2]))

        b = osc.Bundle()
        b.add(m1)
        b.add(osc.Bundle([m2]))
        b.add(osc.Bundle([m3]))
        self.assertEquals(b.getMessages(), set([m1, m2, m3]))

