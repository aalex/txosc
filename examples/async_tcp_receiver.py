#!/usr/bin/env python
"""
Example of a TCP TxOSC receiver with Twisted.

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
    print("Got %s from %s" % (message, address))

class TCPReceiverApplication(object):
    """
    Example that receives UDP OSC messages.
    """
    def __init__(self, port):
        self.port = port
        self.receiver = dispatch.Receiver()
        self.receiver.addCallback("/foo", foo_handler)
        self.receiver.addCallback("/ping", self.ping_handler)
        self.receiver.addCallback("/quit", self.quit_handler)
        self._server_port = reactor.listenTCP(self.port, async.ServerFactory(self.receiver))
        print("Listening on osc.tcp://127.0.0.1:%s" % (self.port))

    def ping_handler(self, message, address):
        """
        Method handler.
        """
        print("Got %s from %s" % (message, address))

    def quit_handler(self, message, address):
        """
        Quits the application.
        """
        print("Got %s from %s" % (message, address))
        reactor.stop()
        print("Goodbye.")

if __name__ == "__main__":
    app = TCPReceiverApplication(17779)
    reactor.run()

