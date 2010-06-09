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
    Function handler for /foo
    """
    print("foo_handler")
    print("  Got %s from %s" % (message, address))

class UDPReceiverApplication(object):
    """
    Example that receives UDP OSC messages.
    """
    def __init__(self, port):
        self.port = port
        self.receiver = dispatch.Receiver()
        self._server_port = reactor.listenUDP(self.port, async.DatagramServerProtocol(self.receiver))
        print("Listening on osc.udp://localhost:%s" % (self.port))
        self.receiver.addCallback("/foo", foo_handler)
        self.receiver.addCallback("/ping", self.ping_handler)
        self.receiver.addCallback("/quit", self.quit_handler)
        self.receiver.addCallback("/ham/egg", self.ham_egg_handler)

        # Now, let's demonstrate how to use address nodes:
        # /cheese:
        self.cheese_node = dispatch.AddressNode("cheese")
        self.cheese_node.addCallback("*", self.cheese_handler)
        self.receiver.addNode("cheese", self.cheese_node)
        # /cheese/cheddar:
        self.cheddar_node = dispatch.AddressNode("cheddar")
        self.cheddar_node.addCallback("*", self.cheese_cheddar_handler)
        self.cheese_node.addNode("cheddar", self.cheddar_node)
        
        # fallback:
        self.receiver.fallback = self.fallback
    
    def cheese_handler(self, message, address):
        """
        Method handler for /ping
        """
        print("cheese_handler")
        print("  Got %s from %s" % (message, address))

    def cheese_cheddar_handler(self, message, address):
        """
        Method handler for /cheese/cheddar
        """
        print("cheese_cheddar_handler")
        print("  Got %s from %s" % (message, address))
    
    def fallback(self, message, address):
        """
        Fallback for any unhandled message
        """
        print("Fallback:")
        print("  Got %s from %s" % (message, address))

    def ping_handler(self, message, address):
        """
        Method handler for /ping
        """
        print("ping_handler")
        print("  Got %s from %s" % (message, address))

    def ham_egg_handler(self, message, address):
        """
        Method handler for /ham/egg
        """
        print("ham_egg_handler")
        print("  Got %s from %s" % (message, address))

    def quit_handler(self, message, address):
        """
        Method handler for /quit
        Quits the application.
        """
        print("quit_handler")
        print("  Got %s from %s" % (message, address))
        reactor.stop()
        print("Goodbye.")

if __name__ == "__main__":
    app = UDPReceiverApplication(17779)
    reactor.run()

