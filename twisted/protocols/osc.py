# -*- test-case-name: twisted.test.test_osc -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC 1.1 Protocol over UDP for Twisted.
http://opensoundcontrol.org/spec-1_1
"""
import string
import math
import struct

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import defer, reactor

class OscError(Exception):
    """
    Any error raised by this module.
    """
    pass


class Message(object):
    """
    OSC Message
    """

    def __init__(self, address, type_tags="", arguments=[]):
        self.address = address
        self.type_tags = type_tags
        self.arguments = arguments

    def toBinary(self):
        return StringArgument(self.address).toBinary() + "," + self.getTypeTags() + "".join([a.toBinary() for a in self.arguments])

    def getTypeTags(self):
        """
        :rettype: string
        """
        return "".join([a.typeTag for a in self.arguments])


class Bundle(object):
    """
    OSC Bundle
    """
    def __init__(self, messages=[],  time_tag=0):
        self.messages = messages
        self.time_tag = time_tag
        if self.time_tag is None:
            pass
            #TODO create time tag
            pass

    def toBinary(self):
        data = "#bundle"
        data += TimeTagArgument(self.time_tag).toBinary()
        for msg in self.messages:
            binary = msg.toBinary()
            data += IntArgument(len(binary)).toBinary()
            data += binary
        return data


class Argument(object):
    """
    Base OSC argument
    """
    typeTag = None  # Must be implemented in children classes

    def __init__(self, value):
        self.value = value


    def toBinary(self):
        """
        Encode the value to binary form, ready to send over the wire.
        """
        raise NotImplemented('Override this method')


    @classmethod
    def fromBinary(self, data):
        """
        Decode the value from binary form. Result is a tuple of (Instance, leftover).
        """
        raise NotImplemented('Override this method')


#
# OSC 1.1 required arguments
#

class BlobArgument(Argument):
    typeTag = "b"

    def toBinary(self):
        sz = len(self.value)
        length = math.ceil((sz+1) / 4.0) * 4
        return struct.pack(">i%ds" % (length), sz, str(self.value))



class StringArgument(Argument):
    typeTag = "s"

    def toBinary(self):
        length = math.ceil((len(self.value)+1) / 4.0) * 4
        return struct.pack(">%ds" % (length), str(self.value))

    @classmethod
    def fromBinary(self, data):
        """
        Parses binary data to get the first string in it.

        Returns a tuple with string, leftover.
        The leftover should be parsed next.
        :rettype: tuple

        OSC-string A sequence of non-null ASCII characters followed by a null, 
            followed by 0-3 additional null characters to make the total number of bits a multiple of 32.
            """
        null_pos = string.find(data, "\0") # find the first null char
        s = data[0:null_pos] # get the first string out of data
        i = null_pos # find the position of the beginning of the next data
        i = i + (4 - (i % 4)) # considering that all data must have a size of a multiple of 4 chars.
        leftover = data[i:]
        return StringArgument(s), leftover


class IntArgument(Argument):
    typeTag = "i"

    def toBinary(self):
        return struct.pack(">i", int(self.value))


class FloatArgument(Argument):
    typeTag = "f"

    def toBinary(self):
        return struct.pack(">f", float(self.value))


class TimeTagArgument(Argument):
    typeTag = "t"

    def toBinary(self):
        fr, sec = math.modf(self.value)
        return struct.pack('>ll', long(sec), long(fr * 1e9))


class BooleanArgument(Argument):
    def __init__(self, value):
        Argument.__init__(self, value)
        if self.value:
            self.typeTag = "T"
        else:
            self.typeTag = "F"

    def toBinary(self):
        return ""


class NullArgument(Argument):
    typeTag = "N"

    def __init__(self):
        self.value = None


class ImpulseArgument(Argument):
    typeTag = "I"

    def __init__(self):
        self.value = None

#
# Optional arguments
#
# Should we implement all types that are listed "optional" in
# http://opensoundcontrol.org/spec-1_0 ?

#class SymbolArgument(StringArgument):
#    typeTag = "S"


#global dicts
_types = {
    float: FloatArgument,
    str: StringArgument,
    int: IntArgument,
    unicode: StringArgument,
    #TODO : more types
    }


_tags = {
    "b": BlobArgument,
    "f": FloatArgument,
    "i": IntArgument,
    "s": StringArgument,
    #TODO : more types
    }

def createArgument(data, type_tag=None):
    """
    Creates an OSC argument, trying to guess its type if no type is given.

    Factory of *Attribute object.
    :param data: Any Python base type.
    :param type_tag: One-letter string. Either "i", "f", etc.
    """
    global _types
    global _tags
    kind = type(data)
    try:
        if type_tag in _tags.keys():
            return _tags[type_tag](data)
        if kind in _types.keys():
            return _types[kind](data)
        else:
            raise OscError("Data %s")
    except ValueError, e:
        raise OscError("Could not cast %s to %s. %s" % (data, type_tag, e.message))


class OscProtocol(DatagramProtocol):
    """
    The OSC server protocol
    """
    def datagramReceived(self, data, (host, port)):
        #The contents of an OSC packet must be either an OSC Message or an OSC Bundle. The first byte of the packet's contents unambiguously distinguishes between these two alternatives.
        packet_type = data[0] # TODO
        print "received %r from %s:%d" % (data, host, port)
        osc_address, leftover = StringArgument.fromBinary(data)
        print("Got OSC address: %s" % (osc_address.value))
        #self.transport.write(data, (host, port))


class OscClientProtocol(DatagramProtocol):
     def __init__(self, onStart):
         self.onStart = onStart

     def startProtocol(self):
         self.onStart.callback(self)


class OscSender(object):
     def __init__(self):
         d = defer.Deferred()
         def listening(proto):
             self.proto = proto
         d.addCallback(listening)
         self._port = reactor.listenUDP(0, OscClientProtocol(d))

     def send(self, msg, (host, port)):
         data = msg.toBinary()
         self.proto.transport.write(data, (host, port))

     def stop(self):
         self._call.stop()
         self._port.stopListening()


# TODO: move to doc/core/examples/oscserver.py
if __name__ == "__main__":
    reactor.listenUDP(17777, OscProtocol())

    ds = OscSender()
    ds.send(Message("/foo"), ("127.0.0.1", 17777))

    reactor.run()
