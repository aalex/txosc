#!/usr/bin/env python
"""
OSC 1.1 Protocol over UDP for Twisted.
http://opensoundcontrol.org/spec-1_1 
"""
# classes:
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
class TimetagArgument(Argument):
    pass
class DoubleArgument(Argument):
    pass
class SymbolArgument(Argument): 
    pass
    #FIXME: what is that?

