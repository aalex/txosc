#!/usr/bin/env python
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.
# TODO: # -*- test-case-name: txosc.test.test_sync -*-
"""
Synchronous implementation of OSC using blocking network Python programming.

Twisted is not used in this file.
"""
import socket
import struct

class _Sender(object):
    def __init__(self):
        self._socket = None

    def send(self, element):
        binary = element.toBinary()
        self._actually_send(struct.pack(">i", len(binary)) + binary)

    def _actually_send(self):
        raise NotImplementedError("This method must be overriden in child classes.")
    def close(self):
        raise NotImplementedError("This method must be overriden in child classes.")

class TcpSender(_Sender):
    def __init__(self, address, port):
        _Sender.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
        self.buffer_size = 1024
        self._socket.connect((self.address, self.port))

    def _actually_send(self, binary_data):
        self._socket.send(binary_data)
        # self._socket.recv(self.buffer_size) #FIXME

    def close(self):
        self._socket.close()

