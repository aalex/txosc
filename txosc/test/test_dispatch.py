# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC tests.

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest
from twisted.internet import reactor, defer, task
from txosc import osc
from txosc import async
from txosc import dispatch


class TestAddressNode(unittest.TestCase):
    """
    Test the L{dispatch.AddressNode}; adding/removing/dispatching callbacks, wildcard matching.
    """

    def testName(self):

        n = dispatch.AddressNode()
        n.setName("the_name")
        self.assertEquals("the_name", n.getName())
        n = dispatch.AddressNode("the_name")
        self.assertEquals("the_name", n.getName())


    def testAddRemoveCallback(self):

        def callback(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo", callback)
        self.assertEquals(n.getCallbacks("/foo"), set([callback]))
        n.removeCallback("/foo", callback)
        self.assertEquals(n.getCallbacks("/foo"), set())

        n.addCallback("/*", callback)
        self.assertEquals(n.getCallbacks("/foo"), set([callback]))
        n.removeCallback("/*", callback)
        self.assertEquals(n.getCallbacks("/foo"), set())


    def testRemoveAllCallbacks(self):

        def callback(m):
            pass
        def callback2(m):
            pass
        def callback3(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo", callback)
        self.assertEquals(n.getCallbacks("/*"), set([callback]))
        n.removeAllCallbacks()
        self.assertEquals(n.getCallbacks("/*"), set())

        n = dispatch.AddressNode()
        n.addCallback("/foo", callback)
        n.addCallback("/foo/bar", callback2)
        n.removeAllCallbacks()
        self.assertEquals(n.getCallbacks("/*"), set([]))


    def testAddInvalidCallback(self):
        n = dispatch.AddressNode()
        self.assertRaises(ValueError, n.addCallback, "/foo bar/baz", lambda m: m)
        self.assertEquals(n.addCallback("/foo/*/baz", lambda m: m), None)


    def testRemoveNonExistingCallback(self):
        n = dispatch.AddressNode()
        self.assertRaises(KeyError, n.removeCallback, "/foo", lambda m: m)

    def testMatchExact(self):

        def callback(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo", callback)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/bar")), set())

    def testMatchCallbackWildcards(self):

        def callback(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo/*", callback)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/bar")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar/baz")), set([]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set([callback]))

        n = dispatch.AddressNode()
        n.addCallback("/*", callback)
        self.assertEquals(n.matchCallbacks(osc.Message("/")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set([]))

        n = dispatch.AddressNode()
        n.addCallback("/*/baz", callback)
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/baz")), set([callback]))

        n = dispatch.AddressNode()
        n.addCallback("/*/*", callback)
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/baz")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar/baz")), set([]))

    def testMatchCallbackRangeWildcards(self):

        def callback1(m): pass
        def callback2(m): pass
        n = dispatch.AddressNode()
        n.addCallback("/foo1", callback1)
        n.addCallback("/foo2", callback2)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo[1]")), set([callback1]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo[1-9]")), set([callback1, callback2]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo[4-6]")), set([]))

    def testMatchMessageWithWildcards(self):

        def fooCallback(m):
            pass
        def barCallback(m):
            pass
        def bazCallback(m):
            pass
        def foobarCallback(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo", fooCallback)
        n.addCallback("/bar", barCallback)
        n.addCallback("/baz", bazCallback)
        n.addCallback("/foo/bar", foobarCallback)

        self.assertEquals(n.matchCallbacks(osc.Message("/*")), set([fooCallback, barCallback, bazCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/spam")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/ba*")), set([barCallback, bazCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/b*r")), set([barCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/ba?")), set([barCallback, bazCallback]))


    def testMatchMessageWithRange(self):

        def firstCallback(m):
            pass
        def secondCallback(m):
            pass
        n = dispatch.AddressNode()
        n.addCallback("/foo/1", firstCallback)
        n.addCallback("/foo/2", secondCallback)

        self.assertEquals(n.matchCallbacks(osc.Message("/baz")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/[1-3]")), set([firstCallback, secondCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/[!1]")), set([secondCallback]))


    def testWildcardMatching(self):

        self.assertFalse(dispatch.AddressNode.matchesWildcard("foo", "bar"))

        self.assertTrue(dispatch.AddressNode.matchesWildcard("", "?"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("f", "?"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("fo", "?"))

        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "f?o"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("fo", "f?o"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("fooo", "f?o"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "f??o"))

        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "*"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "f*"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("fo", "f*o"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "f*o"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("foo", "f*bar"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("foo", "*bar"))

        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "*bar"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "f?ob*r"))


    def testWildcardCharMatching(self):
        self.assertTrue(dispatch.AddressNode.matchesWildcard("abc", "a[b]c"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("abc", "a[bc]c"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("abc", "a[abcdefg][abc]"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("abc", "a[abcdefg][def]"))
        self.assertRaises(osc.OscError, dispatch.AddressNode.matchesWildcard, "abc", "a[abcdefg][def")


    def testWildcardRangeMatching(self):
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar1", "bar[1-3]"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar23", "bar[1-3]3"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar23", "bar[1-3][1-9]"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("bar2", "bar[a-z]"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("bar20", "bar[10-30]"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("a-c", "a[x-]c"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("a-c", "a[x-z]c"))


    def testWildcardRangeNegateMatching(self):
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar", "b[!b]r"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("bar", "b[!b][!a-z]"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("bar23", "bar[!1-3]3"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar2", "bar[!a-z]"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("abc", "a[b!]c"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("a!c", "a[b!]c"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("a!c", "a[!!]c"))


    def testWildcardAnyStringsMatching(self):
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foo", "{foo,bar}"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar", "{foo,bar}"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("bar", "{foo,bar,baz}"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "foo{bar}"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "foo{bar}"))
        self.assertFalse(dispatch.AddressNode.matchesWildcard("bar", "{foo,bar,baz}bar"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "{foo,bar,baz}bar"))
        self.assertTrue(dispatch.AddressNode.matchesWildcard("barbar", "{foo,bar,baz}bar"))


    def testWildcardCombined(self):
        self.assertTrue(dispatch.AddressNode.matchesWildcard("foobar", "f??{abc,ba}[o-s]"))


    def testAddressNodeNesting(self):

        def cb():
            pass
        child = dispatch.AddressNode()
        child.addCallback("/bar", cb)

        parent = dispatch.AddressNode()
        parent.addNode("foo", child)

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        self.assertEquals(parent.getCallbacks("/foo/b*"), set([cb]))
        self.assertEquals(parent.getCallbacks("/foo/baz"), set())

    def testAddressNodeNestingMultiple(self):

        class MyNode(dispatch.AddressNode):
            def __init__(self):
                dispatch.AddressNode.__init__(self)
                self.addCallback("/trigger", self.trigger)

            def trigger(self):
                pass

        c1 = MyNode()
        c2 = MyNode()
        parent = dispatch.AddressNode()
        parent.addNode("foo", c1)
        parent.addNode("bar", c2)

        self.assertEquals(parent.getCallbacks("/foo/*"), set([c1.trigger]))
        self.assertEquals(parent.getCallbacks("/bar/*"), set([c2.trigger]))
        self.assertEquals(parent.getCallbacks("/*/trigger"), set([c1.trigger, c2.trigger]))


    def testAddressNodeRenaming(self):

        def cb():
            pass
        child = dispatch.AddressNode()
        child.addCallback("/bar", cb)

        parent = dispatch.AddressNode()
        parent.addNode("foo", child)

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        child.setName("bar")
        self.assertEquals(parent.getCallbacks("/bar/bar"), set([cb]))


    def testAddressNodeReparenting(self):

        def cb():
            pass
        child = dispatch.AddressNode()
        child.addCallback("/bar", cb)

        baz = dispatch.AddressNode()

        parent = dispatch.AddressNode()
        parent.addNode("foo", child)
        parent.addNode("baz", baz) # empty node

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        child.setParent(baz)
        self.assertEquals(parent.getCallbacks("/foo/bar"), set([]))
        self.assertEquals(parent.getCallbacks("/baz/foo/bar"), set([cb]))



class TestReceiver(unittest.TestCase):
    """
    Test the L{dispatch.Receiver} class.
    """

    def testDispatching(self):

        hello = osc.Message("/hello")
        there = osc.Message("/there")
        addr = ("0.0.0.0", 17778)

        def cb(message, a):
            self.assertEquals(message, hello)
            self.assertEquals(addr, a)
            state['cb'] = True
        def cb2(message, a):
            self.assertEquals(message, there)
            self.assertEquals(addr, a)
            state['cb2'] = True

        recv = dispatch.Receiver()
        recv.addCallback("/hello", cb)
        recv.addCallback("/there", cb2)

        state = {}
        recv.dispatch(hello, addr)
        self.assertEquals(state, {'cb': True})

        state = {}
        recv.dispatch(osc.Bundle([hello, there]), addr)
        self.assertEquals(state, {'cb': True, 'cb2': True})


    def testFunctionFallback(self):
        hello = osc.Message("/hello")
        addr = ("0.0.0.0", 17778)
        
        def cb(message, address):
            self.assertEquals(message, hello)
        
        recv = dispatch.Receiver()
        recv.fallback = cb
        recv.dispatch(hello, addr)
        
    def testClassFallback(self):
        hello = osc.Message("/hello")
        addr = ("0.0.0.0", 17778)
        
        class Dummy(object):
            def __init__(self, test_case):
                self.x = 3
                self.test_case = test_case
            def cb(self, message, address):
                self.test_case.assertEquals(message, hello)
                self.test_case.assertEquals(self.x, 3)
        
        recv = dispatch.Receiver()
        dummy = Dummy(self)
        recv.fallback = dummy.cb
        recv.dispatch(hello, addr)
