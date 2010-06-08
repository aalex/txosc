#!/usr/bin/env python
"""
Example of a UDP TxOSC sender with Twisted.

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
    def __init__(self, port, host="127.0.0.1"):
        self.port = port
        self.host = host
        self.client = async.DatagramClientProtocol()
        self._client_port = reactor.listenUDP(0, self.client)
        reactor.callLater(0, self.send_messages)

    def _send(self, element):
        self.client.send(element, (self.host, self.port))
        print("Sent %s to %s:%d" % (element, self.host, self.port))
        
    def send_messages(self):
        self._send(osc.Message("/ping"))
        self._send(osc.Message("/foo"))
        self._send(osc.Message("/quit"))
        reactor.stop()
        print("Goodbye.")

if __name__ == "__main__":
    app = UDPSenderApplication(17779)
    reactor.run()

