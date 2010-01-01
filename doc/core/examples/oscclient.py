# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

""" Simple OSC client """

import sys
# FIXME - remove this dirty hack
sys.path.insert(0, ".")

from twisted.internet import reactor
from twisted.protocols import osc

if __name__ == "__main__":
    ds = osc.OscSender()
    ds.send(osc.Message("/foo"), ("127.0.0.1", 17777))
    ds.send(osc.Message("/foo", osc.StringArgument("bar")), ("127.0.0.1", 17777))
    ds.send(osc.Bundle([osc.Message("/foo", osc.StringArgument("bar"))]), ("127.0.0.1", 17777))

    reactor.run()
