#!/usr/bin/env python
"""
Example of a UDP txosc sender and receiver with Twisted.

This example is in the public domain.
Written by Alexandre Quessy in 2010.

Usage: Start this script in a shell. Start it again with any argument in an other shell on the same computer.
"""
import sys
from twisted.internet import reactor
from txosc import osc
from txosc import dispatch
from txosc import async

class PingPongApplication(object):
    """
    Example that sends and receives UDP OSC messages.
    """
    def __init__(self, is_initiator=True):
        self.delay = 1.0
        self.send_host = "127.0.0.1"
        self.send_port = 17777
        self.receive_port = 16666
        if is_initiator:
            self.send_port = 16666
            self.receive_port = 17777
            
        self.receiver = dispatch.Receiver()
        self.sender = async.DatagramClientProtocol()
        self._sender_port = reactor.listenUDP(0, self.sender)
        self._server_port = reactor.listenUDP(self.receive_port, async.DatagramServerProtocol(self.receiver))
        print("Listening on osc.udp://localhost:%s" % (self.receive_port))
        self.receiver.addCallback("/ping", self.ping_handler)
        self.receiver.addCallback("/pong", self.pong_handler)
        self.receiver.fallback = self.fallback
        if is_initiator:
            reactor.callLater(0.1, self._start)

    def _start(self):
        """
        Initiates the ping pong game.
        """
        self._send_ping()
    
    def ping_handler(self, message, address):
        """
        Method handler for /ping
        """
        print("Got %s from %s" % (message, address))
        reactor.callLater(self.delay, self._send_pong)

    def pong_handler(self, message, address):
        """
        Method handler for /pong
        """
        print("Got %s from %s" % (message, address))
        reactor.callLater(self.delay, self._send_ping)

    def _send_ping(self):
        """
        Sends /ping
        """
        self.sender.send(osc.Message("/ping"), (self.send_host, self.send_port))
        print("Sent /ping")

    def _send_pong(self):
        """
        Sends /pong
        """
        self.sender.send(osc.Message("/pong"), (self.send_host, self.send_port))
        print("Sent /pong")

    def fallback(self, message, address):
        """
        Fallback for everything else we get.
        """
        print("Lost ball %s from %s" % (message, address))

if __name__ == "__main__":
    is_initiator = False
    if len(sys.argv) > 1:
        is_initiator = True
    app = PingPongApplication(is_initiator)
    reactor.run()

