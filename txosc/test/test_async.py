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


class ClientServerTests(object):
    """
    Common class for the L{TestUDPClientServer} and
    L{TestTCPClientServer} for shared test functions.
    """

    def testSingleMessage(self):
        pingMsg = osc.Message("/ping")
        d = defer.Deferred()

        def ping(m, addr):
            self.assertEquals(m, pingMsg)
            d.callback(True)

        self.receiver.addCallback("/ping", ping)
        self._send(pingMsg)
        return d


    def testBundle(self):

        pingMsg = osc.Message("/ping")
        bundle = osc.Bundle()
        bundle.add(osc.Message("/pong"))
        bundle.add(pingMsg)
        bundle.add(osc.Message("/foo/bar", 1, 2))

        d = defer.Deferred()
        def ping(m, addr):
            self.assertEquals(m, pingMsg)
            d.callback(True)

        d2 = defer.Deferred()
        def foo(m, addr):
            self.assertEquals(m, osc.Message("/foo/bar", 1, 2))
            d2.callback(True)

        self.receiver.addCallback("/ping", ping)
        self.receiver.addCallback("/foo/*", foo)
        self._send(bundle)
        return defer.DeferredList([d, d2])



class TestUDPClientServer(unittest.TestCase, ClientServerTests):
    """
    Test the L{osc.Sender} and L{dispatch.Receiver} over UDP via localhost.
    """
    timeout = 1

    def setUp(self):
        self.receiver = dispatch.Receiver()
        self.serverPort = reactor.listenUDP(17778, async.DatagramServerProtocol(self.receiver))
        self.client = async.DatagramClientProtocol()
        self.clientPort = reactor.listenUDP(0, self.client)


    def tearDown(self):
        return defer.DeferredList([self.serverPort.stopListening(), self.clientPort.stopListening()])


    def _send(self, element):
        self.client.send(element, ("127.0.0.1", 17778))



class TestTCPClientServer(unittest.TestCase, ClientServerTests):
    """
    Test the L{osc.Sender} and L{dispatch.Receiver} over UDP via localhost.
    """
    timeout = 1

    def setUp(self):
        self.receiver = dispatch.Receiver()
        self.serverPort = reactor.listenTCP(17778, async.ServerFactory(self.receiver))
        self.client = async.ClientFactory()
        self.clientPort = reactor.connectTCP("localhost", 17778, self.client)
        return self.client.deferred


    def tearDown(self):
        self.clientPort.transport.loseConnection()
        return defer.DeferredList([self.serverPort.stopListening()])


    def _send(self, element):
        self.client.send(element)



class TestReceiverWithExternalClient(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    # TODO: skip in case of ImportError
    timeout = 1

    def setUp(self):
        self.receiver = dispatch.Receiver()
        self.serverPort = reactor.listenUDP(17778, async.DatagramServerProtocol(self.receiver))
        self.target = liblo.Address(17778)

    def tearDown(self):
        return defer.DeferredList([self.serverPort.stopListening()])

    def testSingleMessage(self):

        d = defer.Deferred()
        def ping(m, addr):
            self.assertEquals(m, osc.Message("/ping"))
            d.callback(True)

        self.receiver.addCallback("/ping", ping)
        liblo.send(self.target, "/ping")
        return d


    def testBundle(self):

        d = defer.Deferred()
        d2 = defer.Deferred()
        def ping(m, addr):
            self.assertEquals(m, osc.Message("/ping"))
            d.callback(True)
        def pong(m, addr):
            self.assertEquals(m, osc.Message("/pong", 1, 2, "string"))
            d2.callback(True)

        self.receiver.addCallback("/ping", ping)
        self.receiver.addCallback("/po*", pong)

        b = liblo.Bundle()
        b.add("/ping")
        b.add("/pong", 1, 2, "string")
        liblo.send(self.target, b)
        return defer.DeferredList([d, d2])



class TestClientWithExternalReceiver(unittest.TestCase):
    """
    This test needs python-liblo.
    """
    timeout = 1

    def setUp(self):
        self.client = async.DatagramClientProtocol()
        self.clientPort = reactor.listenUDP(0, self.client)


    def tearDown(self):
        return defer.DeferredList([self.clientPort.stopListening()])


    def _send(self, element):
        self.client.send(element, ("127.0.0.1", 17778))

    def testSingleMessage(self):
        server = liblo.Server(17779)
        server.start()

        received = False
        def ping_callback(path, args):
            received = True
        server.add_method("/ping", '', ping_callback)

        self._send(osc.Message("/ping"))

        while not received:
            print 11
            server.recv(100)


try:
    import liblo
except ImportError:
    TestReceiverWithExternalClient.skip = "pyliblo not installed"
TestClientWithExternalReceiver.skip = "FIXME: liblo server does not run with twisted"
