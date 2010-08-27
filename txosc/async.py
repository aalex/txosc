#!/usr/bin/env python
# -*- test-case-name: txosc.test.test_async -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
Asynchronous OSC sender and receiver using Twisted
"""
import struct
import socket

from twisted.internet import defer, protocol
from twisted.application.internet import MulticastServer
from txosc.osc import *
from txosc.osc import _elementFromBinary

#
# Stream based client/server protocols
#

class StreamBasedProtocol(protocol.Protocol):
    """
    OSC over TCP sending and receiving protocol.
    """

    def connectionMade(self):
        self.factory.connectedProtocol = self
        if hasattr(self.factory, 'deferred'):
            self.factory.deferred.callback(True)
        self._buffer = ""
        self._pkgLen = None


    def dataReceived(self, data):
        """
        Called whenever data is received.

        In a stream-based protocol such as TCP, the stream should
        begin with an int32 giving the size of the first packet,
        followed by the contents of the first packet, followed by the
        size of the second packet, etc.

        @type data: L{str}
        """
        self._buffer += data
        if len(self._buffer) < 4:
            return
        if self._pkgLen is None:
            self._pkgLen = struct.unpack(">i", self._buffer[:4])[0]
        if len(self._buffer) < self._pkgLen + 4:
            print "waiting for %d more bytes" % (self._pkgLen + 4 - len(self._buffer))
            return
        payload = self._buffer[4:4 + self._pkgLen]
        self._buffer = self._buffer[4 + self._pkgLen:]
        self._pkgLen = None

        if payload:
            element = _elementFromBinary(payload)
            self.factory.gotElement(element)

        if len(self._buffer):
            self.dataReceived("")


    def send(self, element):
        """
        Send an OSC element over the TCP wire.
        @param element: L{txosc.osc.Message} or L{txosc.osc.Bundle}
        """
        binary = element.toBinary()
        self.transport.write(struct.pack(">i", len(binary)) + binary)
        #TODO: return a Deferred



class StreamBasedFactory(object):
    """
    Factory object for the sending and receiving of elements in a
    stream-based protocol (e.g. TCP, serial).

    @ivar receiver:  A L{Receiver} object which is used to dispatch
        incoming messages to.
    @ivar connectedProtocol: An instance of L{StreamBasedProtocol}
        representing the current connection.
    """
    receiver = None
    connectedProtocol = None

    def __init__(self, receiver=None):
        if receiver:
            self.receiver = receiver


    def send(self, element):
        self.connectedProtocol.send(element)


    def gotElement(self, element):
        if self.receiver:
            self.receiver.dispatch(element, self)
        else:
            raise OscError("Element received, but no Receiver in place: " + str(element))

    def __str__(self):
        return str(self.connectedProtocol.transport.client)


class ClientFactory(protocol.ClientFactory, StreamBasedFactory):
    """
    TCP client factory
    """
    protocol = StreamBasedProtocol

    def __init__(self, receiver=None):
        StreamBasedFactory.__init__(self, receiver)
        self.deferred = defer.Deferred()


class ServerFactory(protocol.ServerFactory, StreamBasedFactory):
    """
    TCP server factory
    """
    protocol = StreamBasedProtocol


#
# Datagram client/server protocols
#

class DatagramServerProtocol(protocol.DatagramProtocol):
    """
    The UDP OSC server protocol.

    @ivar receiver: The L{Receiver} instance to dispatch received
        elements to.
    """

    def __init__(self, receiver):
        """
        @param receiver: L{Receiver} instance.
        """
        self.receiver = receiver

    def datagramReceived(self, data, (host, port)):
        element = _elementFromBinary(data)
        self.receiver.dispatch(element, (host, port))

class MulticastDatagramServerProtocol(DatagramServerProtocol):
    """
    UDP OSC server protocol that can listen to multicast.
    
    Here is an example on how to use it:
    
      reactor.listenMulticast(8005, MulticastServerUDP(receiver, "224.0.0.1"), listenMultiple=True)
    
    This way, many listeners can listen on the same port, same host, to the same multicast group. (in this case, the 224.0.0.1 multicast group)
    """
    def __init__(self, receiver, multicast_addr="224.0.0.1"):
        """
        @param multicast_addr: IP address of the multicast group.
        @param receiver: L{txosc.dispatch.Receiver} instance.
        @type multicast_addr: str
        @type receiver: L{txosc.dispatch.Receiver}
        """
        self.multicast_addr = multicast_addr
        DatagramServerProtocol.__init__(self, receiver)
        
    def startProtocol(self):
        """
        Join a specific multicast group, which is the IP we will respond to
        """
        self.transport.joinGroup(self.multicast_addr)

class DatagramClientProtocol(protocol.DatagramProtocol):
    """
    The UDP OSC client protocol.
    """

    def send(self, element, (host, port)):
        """
        Send a L{txosc.osc.Message} or L{txosc.osc.Bundle} to the address specified.
        @type element: L{txosc.osc.Message}
        """
        data = element.toBinary()
        self.transport.write(data, (socket.gethostbyname(host), port))


