# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

""" Simple OSC server. """

from twisted.internet import reactor
from txosc import async, dispatch

if __name__ == "__main__":
    receiver = dispatch.Receiver()
    
    # Adding a simple callback for /ping:
    def ping(msg, addr):
        print "PING! from %s" % repr(addr)
    receiver.addCallback("/ping", ping)
    
    # Adding a callback for /ham/egg:
    def ham_egg(msg, addr):
        print "Ham and egg", msg, addr
    receiver.addCallback("/ham/egg", ham_egg)

    # Adding a callback for any message:
    def fb(msg, addr):
        print "Fallback: ", addr, ":", msg
    receiver.fallback = fb

    # Adding a node for /cheese:
    def cheese(msg, addr):
        print "Got cheese from", addr, ":", msg
    cheeseNode = dispatch.AddressNode("cheese")
    cheeseNode.addCallback("*", cheese) # not only leaves can have callbacks in this implementation of OSC
    receiver.addNode("cheese", cheeseNode)

    # Adding a node for /cheese/cheddar:
    def cheddar(msg, addr):
        print "Got cheddar from", addr, ":", msg

    cheddarNode = dispatch.AddressNode("cheddar")
    cheddarNode.addCallback("*", cheddar)
    cheeseNode.addNode("cheddar", cheddarNode)

    # Starting the server on UDP:
    reactor.listenUDP(17777, async.DatagramServerProtocol(receiver))

    # Starting the server on TCP:
    reactor.listenTCP(17776, async.ServerFactory(receiver))
    print "Listening..."
    reactor.run()
