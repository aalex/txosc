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
    Encoding and decoding of a string argument.
    """
    def testToBinary(self):
        self.assertEqual(osc.BlobArgument("").toBinary(), "\0\0\0\0\0\0\0\0")
        self.assertEqual(osc.BlobArgument("a").toBinary(), "\0\0\0\1a\0\0\0")
        self.assertEqual(osc.BlobArgument("hi").toBinary(), "\0\0\0\2hi\0\0")
        self.assertEqual(osc.BlobArgument("hello").toBinary(), "\0\0\0\5hello\0\0\0")

    def testFromBinary(self):
        data = "\0\0\0\2hi\0\0\0\0\0\5hello\0\0\0"
        first, leftover = osc.BlobArgument.fromBinary(data)
        self.assertEqual(first.value, "hi")
        self.assertEqual(leftover, "\0\0\0\5hello\0\0\0")

        second, leftover = osc.BlobArgument.fromBinary(leftover)
        self.assertEqual(second.value, "hello")
        self.assertEqual(leftover, "")


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
        def test(value):
            int_arg = osc.IntArgument.fromBinary(osc.IntArgument(value).toBinary())[0]
            self.assertEqual(int_arg.value, value)
        test(0)
        test(1)
        test(-1)
        test(1<<31-1)
        test(-1<<31)

    def testIntOverflow(self):
        self.assertRaises(OverflowError, osc.IntArgument(1<<31).toBinary)
        self.assertRaises(OverflowError, osc.IntArgument((-1<<31) - 1).toBinary)


class TestTimeTagArgument(unittest.TestCase):
    def testToBinary(self):
        # 1 second since Jan 1, 1900
        arg = osc.TimeTagArgument(1)
        binary = arg.toBinary()
        self.assertEqual(binary, "\0\0\0\1\0\0\0\0")

    def testFromBinary(self):
        # 1 second since Jan 1, 1900
        val = osc.TimeTagArgument.fromBinary("\0\0\0\1\0\0\0\0")[0].value
        self.assertEqual(val, 1.0)

    def testToAndFromBinary(self):
        # 1 second since Jan 1, 1900
        def test(value):
            timetag_arg, leftover = osc.TimeTagArgument.fromBinary(osc.TimeTagArgument(value).toBinary())
            self.assertEqual(leftover, "")
            #self.assertEqual(value, timetag_arg.value)
            # time tags should not differ more than 200 picoseconds
            delta = 200 * (10 ** -12)
            self.assertTrue(abs(value - timetag_arg.value) <= delta, "Timetag precision")

        test(1.0)
        #test(1.101)

    #testFromBinary.skip = "TimeTagArgument.fromBinary is not yet implemented"


class TestMessage(unittest.TestCase):

    def testEquality(self):
        m = osc.Message("/example")

        m2 = osc.Message("/example")
        self.assertEqual(m, m2)
        m2 = osc.Message("/example2")
        self.assertNotEqual(m, m2)
        m2 = osc.Message("/example", osc.IntArgument(1))
        self.assertNotEqual(m, m2)
        m = osc.Message("/example", osc.IntArgument(1))
        self.assertEqual(m, m2)


    def testGetTypeTag(self):
        m = osc.Message("/example")
        self.assertEqual(m.getTypeTags(), "")
        m.arguments.append(osc.StringArgument("egg"))
        self.assertEqual(m.getTypeTags(), "s")
        m.arguments.append(osc.StringArgument("spam"))
        self.assertEqual(m.getTypeTags(), "ss")

    def testToAndFromBinary(self):

        def test(m):
            binary = m.toBinary()
            m2, leftover = osc.Message.fromBinary(binary)
            self.assertEqual(leftover, "")
            self.assertEqual(len(m.arguments), len(m2.arguments))
            for i in range(len(m.arguments)):
                self.assertEqual(m.arguments[i].value, m2.arguments[i].value)

        test(osc.Message("/example"))
        test(osc.Message("/example", osc.StringArgument("hello")))
        test(osc.Message("/example", osc.IntArgument(1), osc.IntArgument(2), osc.IntArgument(-1)))
        test(osc.Message("/example", osc.BooleanArgument(True)))
        test(osc.Message("/example", osc.BooleanArgument(False), osc.NullArgument(), osc.StringArgument("hello")))


class TestBundle(unittest.TestCase):

    def testEquality(self):
        b = osc.Bundle()
        b2 = osc.Bundle()
        self.assertEqual(b, b2)
        b2.messages.append(osc.Message("/hello"))
        self.assertNotEqual(b, b2)
        b.messages.append(osc.Message("/hello"))
        self.assertEqual(b, b2)

    def testToAndFromBinary(self):
        def test(b):
            binary = b.toBinary()
            b2, leftover = osc.Bundle.fromBinary(binary)
        b = osc.Bundle()
        

class TestAddressSpace(unittest.TestCase):

    def testAddRemoveCallback(self):

        def callback(m):
            pass
        space = osc.AddressSpace()
        space.addCallback("/foo", callback)
        self.assertEqual(space.getCallbacks("/foo"), set([callback]))
        space.removeCallback("/foo", callback)
        self.assertEqual(space.getCallbacks("/foo"), set())

    def testAddInvalidCallback(self):
        space = osc.AddressSpace()
        self.assertRaises(ValueError, space.addCallback, "/foo bar/baz", lambda m: m)
        self.assertEqual(space.addCallback("/foo/*/baz", lambda m: m), None)


    def testRemoveNonExistingCallback(self):
        space = osc.AddressSpace()
        self.assertRaises(KeyError, space.removeCallback, "/foo", lambda m: m)

    def testMatchExact(self):

        def callback(m):
            pass
        space = osc.AddressSpace()
        space.addCallback("/foo", callback)

        self.assertEqual(space.matchCallbacks(osc.Message("/foo")), set([callback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/bar")), set())

    def testMatchCallbackWildcards(self):

        def callback(m):
            pass
        space = osc.AddressSpace()
        space.addCallback("/foo/*", callback)

        self.assertEqual(space.matchCallbacks(osc.Message("/foo")), set())
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/bar")), set([callback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/bar")), set())
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/bar/baz")), set([callback]))

        space = osc.AddressSpace()
        space.addCallback("/*", callback)
        self.assertEqual(space.matchCallbacks(osc.Message("/")), set([callback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/bar")), set([callback]))

        space = osc.AddressSpace()
        space.addCallback("/*/baz", callback)
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/bar")), set())
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/baz")), set([callback]))


    def testMatchMessageWithWildcards(self):

        def fooCallback(m):
            pass
        def barCallback(m):
            pass
        def bazCallback(m):
            pass
        def foobarCallback(m):
            pass
        space = osc.AddressSpace()
        space.addCallback("/foo", fooCallback)
        space.addCallback("/bar", barCallback)
        space.addCallback("/baz", bazCallback)
        space.addCallback("/foo/bar", foobarCallback)

        self.assertEqual(space.matchCallbacks(osc.Message("/*")), set([fooCallback, barCallback, bazCallback, foobarCallback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/spam")), set())
        self.assertEqual(space.matchCallbacks(osc.Message("/ba*")), set([barCallback, bazCallback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/b*r")), set([barCallback]))
        self.assertEqual(space.matchCallbacks(osc.Message("/ba?")), set([barCallback, bazCallback]))


    def testMatchMessageWithRange(self):

        def firstCallback(m):
            pass
        def secondCallback(m):
            pass
        space = osc.AddressSpace()
        space.addCallback("/foo/1", firstCallback)
        space.addCallback("/foo/2", secondCallback)

        self.assertEqual(space.matchCallbacks(osc.Message("/baz")), set())
        self.assertEqual(space.matchCallbacks(osc.Message("/foo/[1-2]")), set([firstCallback, secondCallback]))


    def testWildcardMatching(self):
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "foo"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "*"))
        self.assertFalse(osc.AddressNode.matchesWildcard("foo", "bar"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f*"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f?o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "fo?"))
        self.assertTrue(osc.AddressNode.matchesWildcard("fo", "f*o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f*o"))
        #self.assertTrue(osc.AddressNode.matchesWildcard("bar1", "bar[1-3]"))
        #self.assertFalse(osc.AddressNode.matchesWildcard("bar4", "bar[1-3]"))


    #testMatchCallbackWildcards.skip = "AddressNode matching needs to be implemented"
    #testMatchMessageWithWildcards.skip = "AddressNode matching needs to be implemented"
    testMatchMessageWithRange.skip = "AddressNode range matching needs to be implemented"


class TestServer(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    pass

