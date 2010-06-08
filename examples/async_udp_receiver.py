#!/usr/bin/env python
"""
Example of a UDP TxOSC receiver with Twisted.

This example is in the public domain.
"""
from twisted.internet import reactor
from txosc import osc
from txosc import dispatch
from txosc import async

def foo_handler(message, address):
    """
    Single function handler.
    """
    print("Got /foo")

class UDPReceiverApplication(object):
    """
    Example that receives UDP OSC messages.
    """
    def __init__(self, port):
        self.port = port
        self.receiver = dispatch.Receiver()
        self.serverPort = reactor.listenUDP(self.port, async.DatagramServerProtocol(self.receiver))
        print("Listening on osc.udp://localhost:%s" % (self.port))
        self.receiver.addCallback("/foo", foo_handler)
        self.receiver.addCallback("/ping", self.ping_handler)
        self.receiver.addCallback("/quit", self.quit_handler)

    def ping_handler(self, message, address):
        """
        Method handler.
        """
        print("Got /ping")

    def quit_handler(self, message, address):
        """
        Quits the application.
        """
        print("Got /quit")
        reactor.stop()
        print("Goodbye.")

if __name__ == "__main__":
    app = UDPReceiverApplication(17779)
    reactor.run()

