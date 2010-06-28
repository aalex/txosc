#!/usr/bin/env python
"""
Example of a multicast UDP txosc receiver with Twisted.

You can run many of these on a single host.

This example is in the public domain.
"""
from twisted.internet import reactor
from txosc import osc
from txosc import dispatch
from txosc import async

class MulticastUDPReceiverApplication(object):
    """
    Example that receives multicast UDP OSC messages.
    """
    def __init__(self, port):
        self.port = port
        self.receiver = dispatch.Receiver()
        self._server_port = reactor.listenMulticast(self.port, async.MulticastDatagramServerProtocol(self.receiver, "224.0.0.1"), listenMultiple=True)
        print("Listening on osc.udp://224.0.0.1:%s" % (self.port))
        self.receiver.addCallback("/spam", self.spam_handler)
    
    def spam_handler(self, message, address):
        """
        Method handler for /spam
        """
        print("spam_handler")
        print("  Got %s from %s" % (message, address))

if __name__ == "__main__":
    app = MulticastUDPReceiverApplication(18888)
    reactor.run()

