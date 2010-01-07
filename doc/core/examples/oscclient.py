# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

""" Simple OSC client. """

from twisted.internet import reactor
from twisted.protocols import osc

if __name__ == "__main__":
    ds = osc.Sender()
    ds.send(osc.Message("/ping"), ("127.0.0.1", 17777))

    reactor.run()
