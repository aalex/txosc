# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

""" Simple OSC client. """

from twisted.internet import reactor
from twisted.protocols import osc

if __name__ == "__main__":
    ds = osc.Sender()
    port = 17777
    def send_messages(ds, port):
        # no argument
        ds.send(osc.Message("/ping"), ("127.0.0.1", port))
        # float argument
        ds.send(osc.Message("/ham/egg", 3.14159), ("127.0.0.1", port))
        # str and int arguments
        ds.send(osc.Message("/spam", "hello", 1), ("127.0.0.1", port))
        # NTP timestamp argument. See http://opensoundcontrol.org/spec-1_0
        ds.send(osc.Message("/bacon", osc.TimeTagArgument()), ("127.0.0.1", port))
        # no argument
        ds.send(osc.Message("/cheese"), ("127.0.0.1", port))
        ds.send(osc.Message("/cheese/cheddar"), ("127.0.0.1", port))

        reactor.stop()

    reactor.callLater(0, send_messages, ds, port)
    reactor.run()
