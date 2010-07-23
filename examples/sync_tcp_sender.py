#!/usr/bin/env python
"""
Example of a TCP txosc sender without Twisted.

This example is in the public domain.
"""
import socket # only for the exception type
from txosc import osc
from txosc import sync

if __name__ == "__main__":
    try:
        tcp_sender = sync.TcpSender("localhost", 31337)
    except socket.error, e:
        print(str(e))
    else:
        tcp_sender.send(osc.Message("/hello", 2, "bar", 3.14159))
        tcp_sender.send(osc.Message("/ham/spam", "egg"))
        tcp_sender.close()
        print("Successfully sent the messages.")

