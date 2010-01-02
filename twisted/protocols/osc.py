# -*- test-case-name: twisted.test.test_osc -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC 1.1 Protocol over UDP for Twisted.
Specification : http://opensoundcontrol.org/spec-1_1
Examples : http://opensoundcontrol.org/spec-1_0-examples
"""
import string
import math
import struct
import time
import fnmatch

from twisted.internet import reactor, defer, protocol


class OscError(Exception):
    """
    Any error raised by this module.
    """
    pass


class Message(object):
    """
    An OSC Message element.

    @ivar address: The OSC address string, e.g. "/foo/bar".
    @ivar arguments: List of L{Argument} instances for the message.
    """
    address = None
    arguments = None

    def __init__(self, address, *args):
        self.address = address
        self.arguments = []
        for arg in args:
            self.add(arg)


    def toBinary(self):
        """
        @return: A string with the binary presentation of this message.
        """
        return StringArgument(self.address).toBinary() + StringArgument("," + self.getTypeTags()).toBinary() + "".join([a.toBinary() for a in self.arguments])


    def getTypeTags(self):
        """
        @return: A string  with this message's OSC type tag, e.g. "ii" when there are 2 int arguments.
        """
        return "".join([a.typeTag for a in self.arguments])


    def add(self, value):
        """
        Adds an argument to this message with given value, using L{createArgument}.
        """
        if not isinstance(value, Argument):
            value = createArgument(value)
        self.arguments.append(value)


    @staticmethod
    def fromBinary(data):
        osc_address, leftover = _stringFromBinary(data)
        #print("Got OSC address: %s" % (osc_address))
        message = Message(osc_address)
        type_tags, leftover = _stringFromBinary(leftover)

        if type_tags[0] != ",":
            # invalid type tag string
            raise OscError("Invalid typetag string: %s" % type_tags)

        for type_tag in type_tags[1:]:
            arg, leftover = _argumentFromBinary(type_tag, leftover)
            message.arguments.append(arg)

        return message, leftover


    def __str__(self):
        args = " ".join([str(a) for a in self.arguments])
        return "%s ,%s %s" % (self.address, self.getTypeTags(), args)


    def __eq__(self, other):
        if self.address != other.address:
            return False
        if self.getTypeTags() != other.getTypeTags():
            return False
        if len(self.arguments) != len(other.arguments):
            return False
        for i in range(len(self.arguments)):
            if self.arguments[i].value != other.arguments[i].value:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)


class Bundle(object):
    """
    An OSC Bundle element.
    """
    time_tag = None
    messages = None

    def __init__(self, messages=None,  time_tag=0):
        if messages:
            self.messages = messages
        else:
            self.messages = []

        self.time_tag = time_tag
        if self.time_tag is None:
            pass
            #TODO create time tag

    def toBinary(self):
        data = StringArgument("#bundle").toBinary()
        data += TimeTagArgument(self.time_tag).toBinary()
        for msg in self.messages:
            binary = msg.toBinary()
            data += IntArgument(len(binary)).toBinary()
            data += binary
        return data

    def __eq__(self, other):
        if len(self.messages) != len(other.messages):
            return False
        for i in range(len(self.messages)):
            if self.messages[i] != other.messages[i]:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    @staticmethod
    def fromBinary(data):
        bundleStart, data = _stringFromBinary(data)
        if bundleStart != "#bundle":
            raise OscError("Error parsing bundle string")
        bundle = Bundle()
        bundle.time_tag, data = TimeTagArgument.fromBinary(data)
        while data:
            size, data = IntArgument.fromBinary(data)
            size = size.value
            if len(data) < size:
                raise OscError("Unexpected end of bundle: need %d bytes of data" % size)
            payload = data[:size]
            bundle.messages.append(_elementFromBinary(payload))
            data = data[size:]
        return bundle, ""


    def getMessages(self):
        """
        Retrieve all Message objects from this bundle, recursively.
        """
        r = set()
        for m in self.messages:
            if isinstance(m, Bundle):
                r = r.union(m.getMessages())
            else:
                r.add(m)
        return r


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


    @staticmethod
    def fromBinary(data):
        """
        Decode the value from binary form. Result is a tuple of (Instance, leftover).
        """
        raise NotImplemented('Override this method')

    def __str__(self):
        return "%s:%s " % (self.typeTag, self.value)


#
# OSC 1.1 required arguments
#

class BlobArgument(Argument):
    typeTag = "b"

    def toBinary(self):
        sz = len(self.value)
        #length = math.ceil((sz+1) / 4.0) * 4
        length = _ceilToMultipleOfFour(sz)
        return struct.pack(">i%ds" % (length), sz, str(self.value))
    
    @staticmethod
    def fromBinary(data):
        try:
            length = struct.unpack(">i", data[0:4])[0]
            index_of_leftover = _ceilToMultipleOfFour(length) + 4
            try:
                blob_data = data[4:length + 4]
            except IndexError, e:
                raise OscError("Not enough bytes to find size of a blob of size %s in %s." % (length, data))
        except IndexError, e:
            raise OscError("Not enough bytes to find size of a blob argument in %s." % (data))
        leftover = data[index_of_leftover:]
        return BlobArgument(blob_data), leftover
        


class StringArgument(Argument):
    typeTag = "s"

    def toBinary(self):
        length = math.ceil((len(self.value)+1) / 4.0) * 4
        return struct.pack(">%ds" % (length), str(self.value))

    @staticmethod
    def fromBinary(data):
        """
        Parses binary data to get the first string in it.

        Returns a tuple with string, leftover.
        The leftover should be parsed next.
        :rettype: tuple

        OSC-string A sequence of non-null ASCII characters followed by a null, 
            followed by 0-3 additional null characters to make the total number of bits a multiple of 32.
        """
        value, leftover = _stringFromBinary(data)
        return StringArgument(value), leftover


class IntArgument(Argument):
    typeTag = "i"

    def toBinary(self):
        if self.value >= 1<<31:
            raise OverflowError("Integer too large: %d" % self.value)
        if self.value < -1<<31:
            raise OverflowError("Integer too small: %d" % self.value)
        return struct.pack(">i", int(self.value))

    @staticmethod
    def fromBinary(data):
        try:
            i = struct.unpack(">i", data[:4])[0]
            leftover = data[4:]
        except IndexError, e:
            raise OscError("Too few bytes left to get an int from %s." % (data))
            #FIXME: do not raise error and return leftover anyways ?
        return IntArgument(i), leftover


class FloatArgument(Argument):
    typeTag = "f"

    def toBinary(self):
        return struct.pack(">f", float(self.value))

    @staticmethod
    def fromBinary(data):
        try:
            f = struct.unpack(">f", data[:4])[0]
            leftover = data[4:]
        except IndexError, e:
            raise OscError("Too few bytes left to get a float from %s." % (data))
            #FIXME: do not raise error and return leftover anyways ?
        return FloatArgument(f), leftover


class TimeTagArgument(Argument):
    """
    Time tags are represented by a 64 bit fixed point number. The first 32 bits specify the number of seconds since midnight on January 1, 1900, and the last 32 bits specify fractional parts of a second to a precision of about 200 picoseconds. This is the representation used by Internet NTP timestamps. 

    The time tag value consisting of 63 zero bits followed by a one in the least signifigant bit is a special case meaning "immediately."
    """
    typeTag = "t"
    SECONDS_UTC_TO_UNIX_EPOCH = 2208988800

    def __init__(self, value=None):
        # TODO: call parent's constructor ?
        if value is None:
            #FIXME: is that the correct NTP timestamp ?
            value = self.SECONDS_UTC_TO_UNIX_EPOCH + time.time()
        self.value = value

    def toBinary(self):
        fr, sec = math.modf(self.value)
        return struct.pack('>ll', long(sec), long(fr * 1e9))

    @staticmethod
    def fromBinary(data):
        high, low = struct.unpack(">ll", data[0:8])
        leftover = data[8:]
        time = float(int(high) + low / float(1e9))
        return TimeTagArgument(time), leftover


class BooleanArgument(Argument):
    def __init__(self, value):
        Argument.__init__(self, value)
        if self.value:
            self.typeTag = "T"
        else:
            self.typeTag = "F"

    def toBinary(self):
        return "" # bool args do not have data, just a type tag



class DatalessArgument(Argument):
    """
    An argument whose value is defined just by its type tag.
    """
    typeTag = None # override in subclass
    value = None # override in subclass

    def __init__(self):
        Argument.__init__(self, self.value)

    def toBinary(self):
        return ""

class NullArgument(DatalessArgument):
    typeTag = "N"
    value = None

class ImpulseArgument(DatalessArgument):
    typeTag = "I"
    value = True

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
    bool: BooleanArgument
    #TODO: unicode?: StringArgument,
    #TODO : more types
    }

_tags = {
    "b": BlobArgument,
    "f": FloatArgument,
    "i": IntArgument,
    "s": StringArgument,
    #TODO : more types
    }


def createArgument(value, type_tag=None):
    """
    Creates an OSC argument, trying to guess its type if no type is given.

    Factory of *Attribute objects.
    @param data: Any Python base type.
    @param type_tag: One-letter string. Either "i", "f", etc.
    @return: an Argument instance.
    """
    global _types
    global _tags
    kind = type(value)

    if type_tag:
        # Get the argument type based on given type tag
        if type_tag == "T":
            return BooleanArgument(True)
        if type_tag == "F":
            return BooleanArgument(False)
        if type_tag == "N":
            return NullArgument()
        if type_tag == "I":
            return ImpulseArgument()

        if type_tag in _tags.keys():
            return _tags[type_tag](value)

        raise OscError("Unknown type tag: %s" % type)

    else:
        # Guess the argument type based on the type of the value
        if kind in _types.keys():
            return _types[kind](value)

        raise OscError("No OSC argument type for %s (value = %s)" % (kind, value))



class Receiver(object):
    """
    Receive OSC elements (L{Bundle}s and L{Message}s) from the server
    protocol and handles the matching and dispatching of these to
    registered callbacks.

    Callbacks are stored in a tree-like structure, using L{AddressNode} objects.

    @ivar root: L{AddressNode} instance representing the root of the callback tree.
    """

    root = None

    def __init__(self):
        self.root = AddressNode()


    def getProtocol(self):
        return OscServerProtocol(self)


    def addCallback(self, pattern, callable, typeTags=None):
        """
        Register a callback.

        @param pattern: The pattern to register this callback for.
        @param callable: The callable that will be registered.
        """
        path = self._patternPath(pattern)
        self.root.addCallback(path, callable)


    def removeCallback(self, pattern, callable):
        """
        Remove a single callback.

        @param pattern: The pattern this callback was registered for.
        @param callable: The callable that was registered.
        """
        path = self._patternPath(pattern)
        self.root.removeCallback(path, callable)


    def removeAllCallbacks(self, pattern):
        """
        Remove all callbacks which match with the given pattern.
        """
        raise NotImplementedError("AddressSpace is in progress.")


    def matchCallbacks(self, message):
        """
        Get all callbacks for a given message
        """
        pattern = message.address
        return self.getCallbacks(pattern)


    def getCallbacks(self, pattern):
        """
        Retrieve all callbacks which are bound to given
        pattern. Returns a set() of callables.
        """
        path = self._patternPath(pattern)
        nodes = self.root.match(path)
        if not nodes:
            return nodes
        return reduce(lambda a, b: a.union(b), [n.callbacks for n in nodes])


    def dispatch(self, element, clientAddress):
        """
        Executes every callback matching the message address with Message as argument. 
        (and not only its arguments) 
        The order in which the callbacks are called in undefined.
        -> None
        """
        if isinstance(element, Bundle):
            messages = element.getMessages()
        else:
            messages = [element]
        for m in messages:
            for c in self.getCallbacks(m.address):
                c(m, clientAddress)


    def _messagePath(self, message):
        """
        Given an L{osc.Message}, return the path split up in components.
        """
        return self._patternPath(message.address)


    def _patternPath(self, pattern):
        """
        Given a OSC address path like /foo/bar, return a list of
        ['foo', 'bar']. Note that an OSC address always starts with a
        slash.
        """
        return pattern.split("/")[1:]



class AddressNode(object):
    def __init__(self):
        self.childNodes = {}
        self.callbacks = set()
        self.parent = None
        self.wildcardNodes = set()

    def match(self, path, matchAllChilds = False):
        if not len(path) or matchAllChilds:
            c = set([self])
            if matchAllChilds and self.childNodes:
                c = c.union(reduce(lambda a, b: a.union(b), [n.match(path, True) for n in self.childNodes.values()]))
            return c

        matchedNodes = set()

        part = path[0]
        if AddressNode.isWildcard(part):
            for c in self.childNodes:
                if AddressNode.matchesWildcard(c, part):
                    matchedNodes.add( (self.childNodes[c], part[-1] == "*") )
            # FIXME - what if both the part and some of my childs have wildcards?
        elif self.wildcardNodes:
            matches = set()
            for c in self.wildcardNodes:
                if AddressNode.matchesWildcard(part, c):
                    all = c[-1] == "*" and not self.childNodes[c].childNodes
                    matchedNodes.add( (self.childNodes[c], all) )
                    break
        if part in self.childNodes:
            matchedNodes.add( (self.childNodes[part], False) )

        if not matchedNodes:
            return matchedNodes
        return reduce(lambda a, b: a.union(b), [n.match(path[1:], all) for n, all in matchedNodes])

    def addCallback(self, path, cb):
        if not len(path):
            self.callbacks.add(cb)
        else:
            part = path[0]
            if part not in self.childNodes:
                if not AddressNode.isValidAddressPart(part):
                    raise ValueError("Invalid address part: '%s'" % part)
                self.childNodes[part] = AddressNode()
                if AddressNode.isWildcard(part):
                    self.wildcardNodes.add(part)
            self.childNodes[part].addCallback(path[1:], cb)

    def removeCallback(self, path, cb):
        if not len(path):
            self.callbacks.remove(cb)
        else:
            part = path[0]
            if part not in self.childNodes:
                raise KeyError("No such address part: " + part)
            self.childNodes[part].removeCallback(path[1:], cb)
            if not self.childNodes[part].callbacks and not self.childNodes[part].childNodes:
                # remove child
                if part in self.wildcardNodes:
                    self.wildcardNodes.remove(part)
                del self.childNodes[part]

    @staticmethod
    def isWildcard(part):
        wildcardChars = set("*?[]{}")
        return len(set(part).intersection(wildcardChars)) > 0

    @staticmethod
    def isValidAddressPart(part):
        invalidChars = set(" #,/")
        return len(set(part).intersection(invalidChars)) == 0

    @staticmethod
    def matchesWildcard(value, wildcard):
        if value == wildcard and not AddressNode.isWildcard(wildcard):
            return True
        if wildcard == "*":
            return True

        return fnmatch.fnmatchcase(value, wildcard)


class OscServerProtocol(protocol.DatagramProtocol):
    """
    The OSC server protocol.

    @ivar dispatcher: The dispatcher to dispatch received elements to.
    """
    dispatcher = None

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher


    def datagramReceived(self, data, (host, port)):
        element = _elementFromBinary(data)
        self.dispatcher.dispatch(element, (host, port))



class OscClientProtocol(protocol.DatagramProtocol):
    """
    The OSC client protocol.
    """
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


def _ceilToMultipleOfFour(num):
    """
    Rounds a number to the closest higher number that is a mulitple of four.
    That is for data that need to be padded with zeros so that the length of their data
    must be a multiple of 32 bits.
    """
    return num + (4 - (num % 4)) 


def _argumentFromBinary(type_tag, data):
    if type_tag == "T":
        return BooleanArgument(True), data
    if type_tag == "F":
        return BooleanArgument(False), data
    if type_tag == "N":
        return NullArgument(), data
    if type_tag == "I":
        return ImpulseArgument(), data

    global _tags
    if type_tag not in _tags:
        raise OscError("Invalid typetag: %s" % type_tag)

    return _tags[type_tag].fromBinary(data)


def _stringFromBinary(data):
    null_pos = string.find(data, "\0") # find the first null char
    value = data[0:null_pos] # get the first string out of data
    # find the position of the beginning of the next data
    leftover = data[_ceilToMultipleOfFour(null_pos):]
    return value, leftover


def _elementFromBinary(data):
    if data[0] == "/":
        element, data = Message.fromBinary(data)
    elif data[0] == "#":
        element, data = Bundle.fromBinary(data)
    else:
        raise OscError("Error parsing OSC data: " + data)
    return element
