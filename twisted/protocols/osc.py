#!/usr/bin/env python
"""
OSC 1.1 Protocol over UDP for Twisted.
http://opensoundcontrol.org/spec-1_1 
"""
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class OscError(Exception):
    """
    Any error raised by this module.
    """
    pass

class Message(object):
    """
    OSC Message
    """
    def __init__(self, address, type_tags=None, arguments=None):
        self.address = address
        self.type_tags = type_tags
        self.arguments = arguments

class Bundle(object):
    """
    OSC Bundle
    """
    def __init__(self, messages=[],  time_tag=None):
        self.messages = messages
        self.time_tag = time_tag
        if self.time_tag is None:
            #TODO create time tag

class Argument(object):
    """
    Base OSC argument
    """
    def __init__(self, value):
        self.value = value

class BlobArgument(Argument):
    pass

class StringArgument(Argument):
    pass

class IntArgument(Argument):
    pass

class LongArgument(Argument):
    pass

class FloatArgument(Argument):
    pass

class TimeTagArgument(Argument):
    pass

class DoubleArgument(Argument):
    pass

class SymbolArgument(Argument): 
    pass
    #FIXME: what is that?

#global dicts
_types = {
    float: FloatArgument, 
    str: StringArgument, 
    int: IntArgument, # FIXME: or long?
    unicode: StringArgument, 
    #TODO : more types
    }

_tags = {
    "f": FloatArgument, 
    "s": StringArgument, 
    "i": IntArgument, 
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
        pass
        #print "received %r from %s:%d" % (data, host, port)
        #self.transport.write(data, (host, port))


