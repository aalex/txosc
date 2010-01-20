# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC tests.

Maintainer: Arjan Scherpenisse
"""

from twisted.trial import unittest
from twisted.internet import reactor, defer, protocol
from twisted.protocols import osc

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



class TestAddressNode(unittest.TestCase):
    """
    Test the L{osc.AddressNode}; adding/removing/dispatching callbacks, wildcard matching.
    """

    def testName(self):

        n = osc.AddressNode()
        n.setName("the_name")
        self.assertEquals("the_name", n.getName())
        n = osc.AddressNode("the_name")
        self.assertEquals("the_name", n.getName())


    def testAddRemoveCallback(self):

        def callback(m):
            pass
        n = osc.AddressNode()
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
        n = osc.AddressNode()
        n.addCallback("/foo", callback)
        self.assertEquals(n.getCallbacks("/*"), set([callback]))
        n.removeAllCallbacks("/*")
        self.assertEquals(n.getCallbacks("/*"), set())

        n = osc.AddressNode()
        n.addCallback("/foo", callback)
        n.addCallback("/foo/bar", callback2)
        n.removeAllCallbacks("/foo")
        self.assertEquals(n.getCallbacks("/*"), set([callback2]))


    def testAddInvalidCallback(self):
        n = osc.AddressNode()
        self.assertRaises(ValueError, n.addCallback, "/foo bar/baz", lambda m: m)
        self.assertEquals(n.addCallback("/foo/*/baz", lambda m: m), None)


    def testRemoveNonExistingCallback(self):
        n = osc.AddressNode()
        self.assertRaises(KeyError, n.removeCallback, "/foo", lambda m: m)

    def testMatchExact(self):

        def callback(m):
            pass
        n = osc.AddressNode()
        n.addCallback("/foo", callback)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/bar")), set())

    def testMatchCallbackWildcards(self):

        def callback(m):
            pass
        n = osc.AddressNode()
        n.addCallback("/foo/*", callback)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/bar")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar/baz")), set([callback]))

        n = osc.AddressNode()
        n.addCallback("/*", callback)
        self.assertEquals(n.matchCallbacks(osc.Message("/")), set([callback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set([callback]))

        n = osc.AddressNode()
        n.addCallback("/*/baz", callback)
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/bar")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/baz")), set([callback]))

    def testMatchCallbackRangeWildcards(self):

        def callback1(m): pass
        def callback2(m): pass
        n = osc.AddressNode()
        n.addCallback("/foo1", callback1)
        n.addCallback("/foo2", callback2)

        self.assertEquals(n.matchCallbacks(osc.Message("/foo[1]")), set([callback1]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo[1-10]")), set([callback1, callback2]))
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
        n = osc.AddressNode()
        n.addCallback("/foo", fooCallback)
        n.addCallback("/bar", barCallback)
        n.addCallback("/baz", bazCallback)
        n.addCallback("/foo/bar", foobarCallback)

        self.assertEquals(n.matchCallbacks(osc.Message("/*")), set([fooCallback, barCallback, bazCallback, foobarCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/spam")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/ba*")), set([barCallback, bazCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/b*r")), set([barCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/ba?")), set([barCallback, bazCallback]))


    def testMatchMessageWithRange(self):

        def firstCallback(m):
            pass
        def secondCallback(m):
            pass
        n = osc.AddressNode()
        n.addCallback("/foo/1", firstCallback)
        n.addCallback("/foo/2", secondCallback)

        self.assertEquals(n.matchCallbacks(osc.Message("/baz")), set())
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/[1-10]")), set([firstCallback, secondCallback]))
        self.assertEquals(n.matchCallbacks(osc.Message("/foo/[2-10]")), set([secondCallback]))


    def testWildcardMatching(self):
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "foo"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "*"))
        self.assertFalse(osc.AddressNode.matchesWildcard("foo", "bar"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f*"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f?o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "fo?"))
        self.assertTrue(osc.AddressNode.matchesWildcard("fo", "f*o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f*o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo", "f?o"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foobar", "f?ob*r"))


    def testWildcardRangeMatching(self):
        self.assertTrue(osc.AddressNode.matchesWildcard("bar1", "bar[1-3]"))
        self.assertTrue(osc.AddressNode.matchesWildcard("bar23", "bar[19-30]"))
        self.assertFalse(osc.AddressNode.matchesWildcard("bar4", "bar[1-3]"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo1bar2", "foo[1-3]bar2"))
        self.assertFalse(osc.AddressNode.matchesWildcard("foo5bar2", "foo[1-3]bar2"))
        self.assertTrue(osc.AddressNode.matchesWildcard("foo1bar2", "foo[1-3]bar[1-3]"))
        self.assertFalse(osc.AddressNode.matchesWildcard("foo1bar2", "foo[2-3]bar[1-3]"))
        self.assertTrue(osc.AddressNode.matchesWildcard("bar1001", "bar10[01-10]"))
        self.assertTrue(osc.AddressNode.matchesWildcard("bar101", "bar[1-20]1"))
        self.assertFalse(osc.AddressNode.matchesWildcard("bar101", "bar[1-20]2"))
        self.assertFalse(osc.AddressNode.matchesWildcard("bar101", "bar[1-9]1"))


    def testAddressNodeNesting(self):

        def cb():
            pass
        child = osc.AddressNode()
        child.addCallback("/bar", cb)

        parent = osc.AddressNode()
        parent.addNode("foo", child)

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        self.assertEquals(parent.getCallbacks("/foo/b*"), set([cb]))
        self.assertEquals(parent.getCallbacks("/foo/baz"), set())

    def testAddressNodeNestingMultiple(self):

        class MyNode(osc.AddressNode):
            def __init__(self):
                osc.AddressNode.__init__(self)
                self.addCallback("/trigger", self.trigger)

            def trigger(self):
                pass

        c1 = MyNode()
        c2 = MyNode()
        parent = osc.AddressNode()
        parent.addNode("foo", c1)
        parent.addNode("bar", c2)

        self.assertEquals(parent.getCallbacks("/foo/*"), set([c1.trigger]))
        self.assertEquals(parent.getCallbacks("/bar/*"), set([c2.trigger]))
        self.assertEquals(parent.getCallbacks("/*/trigger"), set([c1.trigger, c2.trigger]))


    def testAddressNodeRenaming(self):

        def cb():
            pass
        child = osc.AddressNode()
        child.addCallback("/bar", cb)

        parent = osc.AddressNode()
        parent.addNode("foo", child)

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        child.setName("bar")
        self.assertEquals(parent.getCallbacks("/bar/bar"), set([cb]))


    def testAddressNodeReparenting(self):

        def cb():
            pass
        child = osc.AddressNode()
        child.addCallback("/bar", cb)

        baz = osc.AddressNode()

        parent = osc.AddressNode()
        parent.addNode("foo", child)
        parent.addNode("baz", baz) # empty node

        self.assertEquals(parent.getCallbacks("/foo/bar"), set([cb]))
        child.setParent(baz)
        self.assertEquals(parent.getCallbacks("/foo/bar"), set([]))
        self.assertEquals(parent.getCallbacks("/baz/foo/bar"), set([cb]))



class TestReceiver(unittest.TestCase):
    """
    Test the L{osc.Receiver} class.
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

        recv = osc.Receiver()
        recv.addCallback("/hello", cb)
        recv.addCallback("/there", cb2)

        state = {}
        recv.dispatch(hello, addr)
        self.assertEquals(state, {'cb': True})

        state = {}
        recv.dispatch(osc.Bundle([hello, there]), addr)
        self.assertEquals(state, {'cb': True, 'cb2': True})


class TestSenderAndReceiver(unittest.TestCase):
    """
    Test the L{osc.Sender} and L{osc.Receiver} over UDP via localhost.
    """

    def setUp(self):
        self.receiver = osc.Receiver()
        self.port = reactor.listenUDP(17778, self.receiver.getProtocol())
        self.sender = osc.Sender()


    def tearDown(self):
        return defer.DeferredList([self.port.stopListening(), self.sender.stop()])


    def _send(self, element):
        self.sender.send(element, ("127.0.0.1", 17778))


    def testSingleElement(self):
        pingMsg = osc.Message("/ping")
        d = defer.Deferred()

        def ping(m, addr):
            self.assertEquals(m, pingMsg)
            d.callback(True)

        self.receiver.addCallback("/ping", ping)
        self._send(pingMsg)
        return d



class TestReceiverWithExternalClient(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    pass


class TestClientWithExternalReceiver(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    pass

class TestTcpLayer(unittest.TestCase):
    def testSingleElement(self):
        pass
    testSingleElement.skip = "We should implement the TCP layer."


    def testWithArguments(self):
        pass
    testWithArguments.skip = "We should implement the TCP layer."

    def testBundle(self):
        pass
    testBundle.skip = "We should implement the TCP layer."



class TestTcpLayer(unittest.TestCase):
    """
    Test the L{osc.TcpSender} and L{osc.OscTcpServerProtocol} over TCP
    """

    def setUp(self):
        def _gotProtocol(proto, self):
            print 'got proto', proto, self
            self.proto = proto

        def _gotServer(serv, self):
            print 'got serv'
        self.receiver = osc.Receiver()
        self.factory = osc.TcpServerFactory(self.receiver)
        p1 = reactor.listenTCP(18888, self.factory)
        #print p1
        #d1.addCallback(_gotServer, self)
        self.client = protocol.ClientCreator(reactor, osc.TcpSender)
        d2 = self.client.connectTCP("localhost", 18888)
        #print d2
        d2.addCallback(_gotProtocol, self)


    def tearDown(self):
        return defer.DeferredList([self.server.transport.loseConnection(), self.proto.transport.lostConnection()])


    def _send(self, element):
        self.proto.sendMessage(element)


    def testSingleElement(self):
        pingMsg = osc.Message("/ping")
        d = defer.Deferred()

        def ping(m, addr):
            self.assertEquals(m, pingMsg)
            d.callback(True)

        self.receiver.addCallback("/ping", ping)
        self._send(pingMsg)
        return d
    testSingleElement.skip = "TCP design not ready"
