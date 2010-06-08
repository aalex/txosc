#!/usr/bin/env python
"""
Example of a TCP TxOSC sender with Twisted.

This example is in the public domain.
"""
from twisted.internet import reactor
from txosc import osc
from txosc import dispatch
from txosc import async

class TCPSenderApplication(object):
    """
    Example that sends UDP messages.
    """
    def __init__(self, port, host="127.0.0.1"):
        self.port = port
        self.host = host
        self.client = async.ClientFactory()
        self._client_port = None

        def _callback(result):
            print("Connected.")
            self.send_messages()

        def _errback(reason):
            print("An error occurred: %s" % (reason.getErrorMessage()))

        self._client_port = reactor.connectTCP(self.host, self.port, self.client)
        self.client.deferred.addCallback(_callback)
        self.client.deferred.addErrback(_errback)

    def _send(self, element):
        self.client.send(element)
        print("Sent %s to %s:%d" % (element, self.host, self.port))
        
    def send_messages(self):
        self._send(osc.Message("/ping"))
        self._send(osc.Message("/foo"))
        self._send(osc.Message("/quit"))
        reactor.callLater(0.1, self.quit)

    def quit(self):
        reactor.stop()
        print("Goodbye.")

if __name__ == "__main__":
    app = TCPSenderApplication(17779)
    reactor.run()

