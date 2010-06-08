# -*- test-case-name: txosc.test.test_osc -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
Asynchronous implementation of OSC for Twisted
"""
import string
import math
import struct
import re

from twisted.internet import reactor, defer, protocol
from txosc.osc import *
from txosc.osc import _elementFromBinary

#
# Stream based client/server protocols
#

class StreamBasedProtocol(protocol.Protocol):

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
            print "waiting for %d more bytes" % (self._pkgLen+4 - len(self._buffer))
            return
        payload = self._buffer[4:4+self._pkgLen]
        self._buffer = self._buffer[4+self._pkgLen:]
        self._pkgLen = None

        if payload:
            element = _elementFromBinary(payload)
            self.factory.gotElement(element)

        if len(self._buffer):
            self.dataReceived("")


    def send(self, element):
        """
        Send an OSC element over the TCP wire.
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


class ClientFactory(protocol.ClientFactory, StreamBasedFactory):
    protocol = StreamBasedProtocol

    def __init__(self, receiver=None):
        StreamBasedFactory.__init__(self, receiver)
        self.deferred = defer.Deferred()


class ServerFactory(protocol.ServerFactory, StreamBasedFactory):
    protocol = StreamBasedProtocol
    # TODO: implement __str__ and return an OSC address as a str



#
# Datagram client/server protocols
#

class DatagramServerProtocol(protocol.DatagramProtocol):
    """
    The OSC server protocol.

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



class DatagramClientProtocol(protocol.DatagramProtocol):
    """
    The OSC datagram-based client protocol.
    """

    def send(self, element, (host, port)):
        """
        Send a L{Message} or L{Bundle} to the address specified.
        """
        data = element.toBinary()
        self.transport.write(data, (host, port))

