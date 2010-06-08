# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

""" Simple OSC client. """

from twisted.internet import reactor
from txosc import dispatch, osc, async

if __name__ == "__main__":

    # send over UDP
    ds = async.DatagramClientProtocol()
    reactor.listenUDP(0, ds)

    def send_udp():
        print "sending UDP..."
        # no argument
        ds.send(osc.Message("/ping"), ("127.0.0.1", 17777))
        # float argument
        ds.send(osc.Message("/ham/egg", 3.14159), ("127.0.0.1", 17777))

    reactor.callLater(0.1, send_udp)

    # send over TCP
    client = async.ClientFactory()
    reactor.connectTCP("localhost", 17776, client)

    def send_tcp():
        print "sending TCP..."
        # str and int arguments
        client.send(osc.Message("/spam", "hello", 1))
        # NTP timestamp argument. See http://opensoundcontrol.org/spec-1_0
        client.send(osc.Message("/bacon", osc.TimeTagArgument()))
        # no argument
        client.send(osc.Message("/cheese"))
        client.send(osc.Message("/cheese/cheddar"))

        reactor.callLater(0.1, reactor.stop)

    reactor.callLater(0.2, send_tcp)

    reactor.run()
