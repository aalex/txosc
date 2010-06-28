#!/usr/bin/env python
"""
Example of a UDP txosc sender with Twisted.

This example is in the public domain.
"""
from twisted.internet import reactor
from txosc import osc
from txosc import dispatch
from txosc import async

class UDPSenderApplication(object):
    """
    Example that sends UDP messages.
    """
    def __init__(self, port, host="224.0.0.1"):
        self.port = port
        self.host = host
        self.client = async.DatagramClientProtocol()
        self._client_port = reactor.listenUDP(0, self.client)
        reactor.callLater(0, self.send_messages)

    def _send(self, element):
        # This method is defined only to simplify the example
        self.client.send(element, (self.host, self.port))
        print("Sent %s to %s:%d" % (element, self.host, self.port))
        
    def send_messages(self):
        self._send(osc.Message("/spam", "How are you?", 3.14159, True))
        print("Goodbye.")
        def _stop():
            reactor.stop()
        reactor.callLater(0.1, _stop)

if __name__ == "__main__":
    app = UDPSenderApplication(18888)
    reactor.run()

