# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

""" Simple OSC server. """

from twisted.internet import reactor
from twisted.protocols import osc

if __name__ == "__main__":
    receiver = osc.Receiver()
    
    # Adding a simple callback for /ping:
    def ping(msg, addr):
        print "PING!", msg, addr
    receiver.addCallback("/ping", ping)
    
    # Adding a callback for /ham/egg:
    def ham_egg(msg, addr):
        print "Ham and egg", msg, addr
    receiver.addCallback("/ham/egg", ham_egg)

    # Adding a callback for any message:
    # (note that it is called on every incoming message)
    def prnt(msg, addr):
        print "Catch-all: ", addr, ":", msg
    receiver.addCallback("/*", prnt)

    # Adding a node for /cheese:
    def cheese(msg, addr):
        print "Got cheese from", addr, ":", msg
    cheeseNode = osc.AddressNode("cheese")
    cheeseNode.addCallback("*", cheese) # not only leaves can have callbacks in this implementation of OSC
    receiver.addNode("cheese", cheeseNode)

    # Adding a node for /cheese/cheddar:
    def cheddar(msg, addr):
        print "Got cheddar from", addr, ":", msg
    cheddarNode = osc.AddressNode("cheddar")
    cheddarNode.addCallback("*", cheddar)
    cheeseNode.addNode("cheddar", cheddarNode)
    
    # Starting the server:
    reactor.listenUDP(17777, receiver.getProtocol())
    reactor.run()
