#!/usr/bin/env python
"""
Example of a TCP txosc sender without Twisted.

This example is in the public domain.
"""
#FIXME: The txosc.sync.UdpSender is currently broken!

import socket # only for the exception type
from txosc import osc
from txosc import sync

if __name__ == "__main__":
    try:
        udp_sender = sync.UdpSender("localhost", 31337)
    except socket.error, e:
        print(str(e))
    else:
        udp_sender.send(osc.Message("/hello", 2, "bar", 3.14159))
        udp_sender.send(osc.Message("/ham/spam", "egg"))
        udp_sender.close()
        print("Successfully sent the messages.")

