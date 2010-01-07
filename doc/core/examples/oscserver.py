# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

""" Simple OSC server. """

from twisted.internet import reactor
from twisted.protocols import osc

if __name__ == "__main__":
    receiver = osc.Receiver()

    def ping(msg, addr):
        print "PING!"
        print msg, addr
    receiver.addCallback("/ping", ping)
    def prnt(msg, addr):
        print "Message from", addr, ":", msg
    receiver.addCallback("/*", prnt)

    reactor.listenUDP(17777, receiver.getProtocol())
    reactor.run()
