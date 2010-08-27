
#!/usr/bin/env python
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.
# TODO: # -*- test-case-name: txosc.test.test_sync -*-
"""
Synchronous blocking OSC sender without Twisted.

Twisted is not used in this file. You don't even need to repy on Twisted to use 
it and the txosc.osc module. That is enough to send OSC messages in a simple
script. 
"""
import socket
import struct

#TODO: receiver
#TODO: bidirectional sender-receiver
# self._socket.recv(self.buffer_size)
# self.buffer_size = 1024

class _Sender(object):
    def __init__(self):
        self._socket = None

    def send(self, element):
        binary = element.toBinary()
        self._actually_send(binary)

    def _actually_send(self, binary_data):
        """
        @param binary_data: Binary blob of an element to send.
        """
        raise NotImplementedError("This method must be overriden in child classes.")
    
    def close(self):
        raise NotImplementedError("This method must be overriden in child classes.")
    


class TcpSender(_Sender):
    """
    Send OSC over TCP using low-level Python socket tools.
    """
    def __init__(self, address, port):
        _Sender.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
        self._socket.connect((self.address, self.port))

    def _actually_send(self, binary_data):
        #For TCP, we need to pack the data with its size first
        data = struct.pack(">i", len(binary_data)) + binary_data
        self._socket.send(data)

    def close(self):
        self._socket.close()

UDP_MODE_MULTICAST = "multicast"
UDP_MODE_BROADCAST = "broadcast"

class UdpSender(_Sender):
    """
    Uses UDP.

    Mode can be either UDP_MODE_BROADCAST or UDP_MODE_MULTICAST or None.
    If using UDP_MODE_MULTICAST, you must set the multicast_group.
    
    FIXME: Right now, the data it sends is badly formatted.
    """
    def __init__(self, address, port, mode=None, multicast_group=None):
        """
        @param multicast_group: IP of the multicast group.
        @type multicast_group: C{str}
        """
        _Sender.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = socket.gethostbyname(address)
        self.port = port
        self._socket.bind(('', 0))
        self.mode = mode
        self.multicast_group = None
        if self.mode == UDP_MODE_MULTICAST:
            if multicast_group is None:
                raise RuntimeError("You must set the multicast group.")
            self.multicast_group = multicast_group
            ttl = struct.pack('b', 1)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            # TODO
        elif self.mode == UDP_MODE_BROADCAST:
            if multicast_group is not None:
                raise RuntimeError("Not using the multicast mode.")
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        else:
            if multicast_group is not None:
                raise RuntimeError("Not using the multicast mode.")

    def _actually_send(self, binary_data):
        # For UDP, we just send the data. 
        # No need to pack it with its size. 
        if self.mode == UDP_MODE_BROADCAST:
            self._socket.sendto(binary_data, ('<broadcast>', self.port))
        elif self.mode == UDP_MODE_MULTICAST:
            self._socket.sendto(binary_data, (self.multicast_group, self.port))
        else:
            self._socket.sendto(binary_data, (self.address, self.port))

    def close(self):
        self._socket.close()

