# -*- test-case-name: twisted.test.test_osc -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC 1.1 Protocol over UDP for Twisted.

The protocol is specified in OSC 1.0 specification at
U{http://opensoundcontrol.org/spec-1_0} and has been further extended
in the paper which can be found at U{http://opensoundcontrol.org/spec-1_1}.
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

    @ivar address: The OSC address string, e.g. C{"/foo/bar"}.
    @type address: C{str}
    @ivar arguments: The L{Argument} instances for the message.
    @type argument: C{list}
    """

    def __init__(self, address, *args):
        self.address = address
        self.arguments = []
        for arg in args:
            self.add(arg)


    def toBinary(self):
        """
        Encodes the L{Message} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Message}.
        """
        return StringArgument(self.address).toBinary() + StringArgument("," + self.getTypeTags()).toBinary() + "".join([a.toBinary() for a in self.arguments])


    def getTypeTags(self):
        """
        Return the OSC type tags for this message.

        @return: A string with this message's OSC type tag, e.g. C{"ii"} when there are 2 int arguments.
        """
        return "".join([a.typeTag for a in self.arguments])


    def add(self, value):
        """
        Adds an argument to this message with given value, using L{createArgument}.

        @param value: Argument to add to this message. Can be any
        Python type, or an L{Argument} instance.
        """
        if not isinstance(value, Argument):
            value = createArgument(value)
        self.arguments.append(value)


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Message} object from binary data that is passed to it.

        This static method is a factory for L{Message} objects.
        It checks the type tags of the message, and parses each of its
        arguments, calling each of the proper factory.

        @param data: String of bytes/characters formatted following the OSC protocol.
        @type data: C{str}
        @return: Two-item tuple with L{Message} as the first item, and the
        leftover binary data, as a L{str}.
        """
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
        s = self.address
        if self.arguments:
            args = " ".join([str(a) for a in self.arguments])
            s += " ,%s %s" % (self.getTypeTags(), args)
        return s


    def __eq__(self, other):
        if self.address != other.address:
            return False
        if len(self.arguments) != len(other.arguments):
            return False
        if self.getTypeTags() != other.getTypeTags():
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

    @ivar timeTag: A L{TimeTagArgument}, representing the time for this bundle.
    @ivar elements: A C{list} of OSC elements (L{Message} or L{Bundle}s).
    """
    timeTag = None
    elements = None

    def __init__(self, elements=None,  timeTag=0):
        if elements:
            self.elements = elements
        else:
            self.elements = []

        self.timeTag = timeTag


    def toBinary(self):
        """
        Encodes the L{Bundle} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Bundle}.
        """
        data = StringArgument("#bundle").toBinary()
        data += TimeTagArgument(self.timeTag).toBinary()
        for msg in self.elements:
            binary = msg.toBinary()
            data += IntArgument(len(binary)).toBinary()
            data += binary
        return data


    def add(self, element):
        """
        Add an element to this bundle.

        @param element: A L{Message} or a L{Bundle}.
        """
        self.elements.append(element)


    def __eq__(self, other):
        if len(self.elements) != len(other.elements):
            return False
        for i in range(len(self.elements)):
            if self.elements[i] != other.elements[i]:
                return False
        return True


    def __ne__(self, other):
        return not (self == other)


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Bundle} object from binary data that is passed to it.

        This static method is a factory for L{Bundle} objects.

        @param data: String of bytes formatted following the OSC protocol.
        @return: Two-item tuple with L{Bundle} as the first item, and the
        leftover binary data, as a L{str}. That leftover should be an empty string.
        """
        bundleStart, data = _stringFromBinary(data)
        if bundleStart != "#bundle":
            raise OscError("Error parsing bundle string")
        bundle = Bundle()
        bundle.timeTag, data = TimeTagArgument.fromBinary(data)
        while data:
            size, data = IntArgument.fromBinary(data)
            size = size.value
            if len(data) < size:
                raise OscError("Unexpected end of bundle: need %d bytes of data" % size)
            payload = data[:size]
            bundle.elements.append(_elementFromBinary(payload))
            data = data[size:]
        return bundle, ""


    def getMessages(self):
        """
        Retrieve all L{Message} elements from this bundle, recursively.

        @return: L{set} of L{Message} instances.
        """
        r = set()
        for m in self.elements:
            if isinstance(m, Bundle):
                r = r.union(m.getMessages())
            else:
                r.add(m)
        return r


class Argument(object):
    """
    Base OSC argument class.

    @ivar typeTag: A 1-character C{str} which represents the OSC type
    of this argument. Every subclass must define its own typeTag.
    """
    typeTag = None

    def __init__(self, value):
        self.value = value


    def toBinary(self):
        """
        Encodes the L{Argument} to binary form, ready to send over the wire.

        @return: A string with the binary presentation of this L{Message}.
        """
        raise NotImplementedError('Override this method')


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{Message} object from binary data that is passed to it.

        This static method is a factory for L{Argument} objects.
        Each subclass of the L{Argument} class implements it to create an
        instance of its own type, parsing the data given as an argument.

        @param data: C{str} of bytes formatted following the OSC protocol.
        @return: Two-item tuple with L{Argument} as the first item, and the
        leftover binary data, as a L{str}.
        """
        raise NotImplementedError('Override this method')


    def __str__(self):
        return "%s:%s " % (self.typeTag, self.value)


#
# OSC 1.1 required arguments
#

class BlobArgument(Argument):
    """
    An L{Argument} representing arbitrary binary data.
    """
    typeTag = "b"

    def toBinary(self):
        """
        See L{Argument.toBinary}.
        """
        sz = len(self.value)
        #length = math.ceil((sz+1) / 4.0) * 4
        length = _ceilToMultipleOfFour(sz)
        return struct.pack(">i%ds" % (length), sz, str(self.value))


    @staticmethod
    def fromBinary(data):
        """
        See L{Argument.fromBinary}.
        """
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
    """
    An argument representing a C{str}.
    """

    typeTag = "s"

    def toBinary(self):
        length = math.ceil((len(self.value)+1) / 4.0) * 4
        return struct.pack(">%ds" % (length), str(self.value))


    @staticmethod
    def fromBinary(data):
        """
        Creates a L{StringArgument} object from binary data that is passed to it.

        This static method is a factory for L{StringArgument} objects.

        OSC-string A sequence of non-null ASCII characters followed by a null,
        followed by 0-3 additional null characters to make the total number
        of bits a multiple of 32.

        @param data: String of bytes/characters formatted following the OSC protocol.
        @return: Two-item tuple with L{StringArgument} as the first item, and the leftover binary data, as a L{str}.

        """
        value, leftover = _stringFromBinary(data)
        return StringArgument(value), leftover



class IntArgument(Argument):
    """
    An L{Argument} representing a 32-bit signed integer.
    """
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
    """
    An L{Argument} representing a 32-bit floating-point value.
    """

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
    An L{Argument} representing an OSC time tag.

    Like NTP timestamps, time tags are represented by a 64 bit fixed
    point number. The first 32 bits specify the number of seconds
    since midnight on January 1, 1900, and the last 32 bits specify
    fractional parts of a second to a precision of about 200
    picoseconds. This is the representation used by Internet NTP
    timestamps.

    The time tag value consisting of 63 zero bits followed by a one in
    the least signifigant bit is a special case meaning "immediately."
    """
    typeTag = "t"
    SECONDS_UTC_TO_UNIX_EPOCH = 2208988800

    def __init__(self, value=None):
        if value is None:
            #FIXME: is that the correct NTP timestamp ?
            value = self.SECONDS_UTC_TO_UNIX_EPOCH + time.time()
        self.value = value


    def toBinary(self):
        fr, sec = math.modf(self.value)
        # FIXME: DeprecationWarning: struct integer overflow masking is deprecated. 
        return struct.pack('>ll', long(sec), long(fr * 1e9))


    @staticmethod
    def fromBinary(data):
        high, low = struct.unpack(">ll", data[0:8])
        leftover = data[8:]
        time = float(int(high) + low / float(1e9))
        return TimeTagArgument(time), leftover



class BooleanArgument(Argument):
    """
    An L{Argument} representing C{True} or C{False}.
    """

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
    Abstract L{Argument} class for defining arguments whose value is
    defined just by its type tag.

    This class should not be used directly. It is intended to gather
    common behaviour of L{NullArgument} and L{ImpulseArgument}.
    """

    def __init__(self, ignoreValue=None):
        Argument.__init__(self, self.value)


    def toBinary(self):
        return ""



class NullArgument(DatalessArgument):
    """
    An L{Argument} representing C{None}.
    """
    typeTag = "N"
    value = None



class ImpulseArgument(DatalessArgument):
    """
    An L{Argument} representing the C{"bang"} impulse.
    """
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
    bool: BooleanArgument,
    type(None): NullArgument,
    }

_tags = {
    "b": BlobArgument,
    "f": FloatArgument,
    "i": IntArgument,
    "s": StringArgument,
    "t": TimeTagArgument,
    }


def createArgument(value, type_tag=None):
    """
    Creates an OSC argument, trying to guess its type if no type is given.

    Factory of *Attribute objects.
    @param value: Any Python base type.
    @param type_tag: One-letter string. One of C{"sifbTFNI"}.
    @type type_tag: One-letter string.
    @return: Returns an instance of one of the subclasses of the L{Argument} class.
    @rtype: L{Argument} subclass.
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



class AddressNode(object):
    """
    A node in the tree of OSC addresses.

    @ivar _name: the name of this node.
    @ivar _parent: the parent node.
    """

    def __init__(self, name=None, parent=None):
        self._name = name
        self._parent = parent
        self._childNodes = {}
        self._callbacks = set()
        self._parent = None
        self._wildcardNodes = set()


    def removeCallbacks(self):
        """
        Remove all callbacks from this node.
        """
        self._callbacks = set()
        self._checkRemove()


    def setName(self, newname):
        """
        Give this node a new name.
        """
        if self._parent:
            del self._parent._childNodes[self._name]
        self._name = newname
        if self._parent:
            self._parent._childNodes[self._name] = self


    def setParent(self, newparent):
        """
        Reparent this node to another parent.
        """
        if self._parent:
            del self._parent._childNodes[self._name]
            self._parent._checkRemove()
        self._parent = newparent
        self._parent._childNodes[self._name] = self


    def _checkRemove(self):
        if not self._parent:
            return
        if not self._callbacks and not self._childNodes:
            del self._parent._childNodes[self._name]
        self._parent._checkRemove()


    def addNode(self, name, instance):
        """
        Add a child node.
        """
        instance.setName(name)
        instance.setParent(self)


    def getName(self):
        return self._name


    def match(self, pattern, _matchAllChilds = False):
        """
        Match a pattern to return a set of nodes.

        @param pattern: A C{str} with an address pattern.
        @return a C{set()} of matched AddressNode instances.
        """

        path = self._patternPath(pattern)
        if not len(path) or _matchAllChilds:
            c = set([self])
            if _matchAllChilds and self._childNodes:
                c = c.union(reduce(lambda a, b: a.union(b), [n.match(path, True) for n in self._childNodes.values()]))
            return c

        matchedNodes = set()

        part = path[0]
        if AddressNode.isWildcard(part):
            for c in self._childNodes:
                if AddressNode.matchesWildcard(c, part):
                    matchedNodes.add( (self._childNodes[c], part[-1] == "*") )
            # FIXME - what if both the part and some of my childs have wildcards?
        elif self._wildcardNodes:
            matches = set()
            for c in self._wildcardNodes:
                if AddressNode.matchesWildcard(part, c):
                    all = c[-1] == "*" and not self._childNodes[c]._childNodes
                    matchedNodes.add( (self._childNodes[c], all) )
                    break
        if part in self._childNodes:
            matchedNodes.add( (self._childNodes[part], False) )

        if not matchedNodes:
            return matchedNodes
        return reduce(lambda a, b: a.union(b), [n.match(path[1:], all) for n, all in matchedNodes])


    def addCallback(self, pattern, cb):
        """
        Adds a callback for L{Message} instances received for a given OSC path.
        @param path: OSC address in the form C{/egg/spam/ham}, or list C{['egg', 'spam', 'ham']}.
        @type pattern: C{str} or C{list}.
        @param cb: Callback that will receive L{Message} as an argument when received.
        @type cb: Function of method.
        @return: None
        """
        path = self._patternPath(pattern)
        if not len(path):
            self._callbacks.add(cb)
        else:
            part = path[0]
            if part not in self._childNodes:
                if not AddressNode.isValidAddressPart(part):
                    raise ValueError("Invalid address part: '%s'" % part)
                self.addNode(part, AddressNode())
                if AddressNode.isWildcard(part):
                    self._wildcardNodes.add(part)
            self._childNodes[part].addCallback(path[1:], cb)


    def removeCallback(self, pattern, cb):
        """
        Removes a callback for L{Message} instances received for a given OSC path.

        @param path: OSC address in the form C{/egg/spam/ham}, or list C{['egg', 'spam', 'ham']}.
        @type pattern: C{str} or C{list}.
        @param cb: Callback that will receive L{Message} as an argument when received.
        @type cb: A callable object.
        """
        path = self._patternPath(pattern)
        if not len(path):
            self._callbacks.remove(cb)
        else:
            part = path[0]
            if part not in self._childNodes:
                raise KeyError("No such address part: " + part)
            self._childNodes[part].removeCallback(path[1:], cb)
            if not self._childNodes[part]._callbacks and not self._childNodes[part]._childNodes:
                # remove child
                if part in self._wildcardNodes:
                    self._wildcardNodes.remove(part)
                del self._childNodes[part]


    @staticmethod
    def isWildcard(name):
        """
        Given a name, returns whether it contains wildcard characters.
        """
        wildcardChars = set("*?[]{}")
        return len(set(name).intersection(wildcardChars)) > 0


    @staticmethod
    def isValidAddressPart(part):
        """
        Check whether the address part can be used as an L{AddressNode} name.
        @rtype bool
        """
        invalidChars = set(" #,/")
        return len(set(part).intersection(invalidChars)) == 0


    @staticmethod
    def matchesWildcard(value, wildcard):
        """
        Match a value to a wildcard.
        """
        if value == wildcard and not AddressNode.isWildcard(wildcard):
            return True
        if wildcard == "*":
            return True

        return fnmatch.fnmatchcase(value, wildcard)


    def _patternPath(self, pattern):
        """
        Given a OSC address path like /foo/bar, return a list of
        ['foo', 'bar']. Note that an OSC address always starts with a
        slash. If a list is input, it is output directly.

        @param pattern: A L{str} OSC address.
        @return: A L{list} of L{str}. Each part of an OSC path.
        """
        if type(pattern) == list:
            return pattern
        return pattern.split("/")[1:]


    def removeAllCallbacks(self, pattern="/*"):
        """
        Remove all callbacks with the given pattern.

        @param pattern: The pattern to match the callbacks. When
        ommited, removes all callbacks.
        """
        path = self._patternPath(pattern)
        nodes = self.match(path)
        for n in nodes:
            n.removeCallbacks()


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
        @return: L{set} of callbables.
        """
        path = self._patternPath(pattern)
        nodes = self.match(path)
        if not nodes:
            return nodes
        return reduce(lambda a, b: a.union(b), [n._callbacks for n in nodes])



class Receiver(AddressNode):
    """
    Receive OSC elements (L{Bundle}s and L{Message}s) from the server
    protocol and handles the matching and dispatching of these to the
    registered callbacks.

    Callbacks are stored in a tree-like structure, using L{AddressNode} objects.
    """

    def getProtocol(self):
        """
        Factory method which creates an L{OscServerProtocol} instance tied to this L{Receiver}.

        @rtype: L{OscServerProtocol}
        """
        return OscServerProtocol(self)


    def dispatch(self, element, clientAddress):
        """
        Dispatch an element to all matching callbacks.

        Executes every callback matching the message address with
        element as argument. The order in which the callbacks are
        called is undefined.

        @param element: A L{Message} or L{Bundle}.
        """
        if isinstance(element, Bundle):
            messages = element.getMessages()
        else:
            messages = [element]
        for m in messages:
            for c in self.getCallbacks(m.address):
                c(m, clientAddress)



class OscServerProtocol(protocol.DatagramProtocol):
    """
    The OSC server protocol.

    @ivar receiver: The L{Receiver} instance to dispatch received elements to.
    """

    def __init__(self, receiver):
        self.receiver = receiver


    def datagramReceived(self, data, (host, port)):
        element = _elementFromBinary(data)
        self.receiver.dispatch(element, (host, port))



class OscClientProtocol(protocol.DatagramProtocol):
    """
    The OSC client protocol.
    """
    def __init__(self, onStart):
        self.onStart = onStart


    def startProtocol(self):
        self.onStart.callback(self)



class Sender(object):
    """
    Sends OSC messages to any destination.

    An instance of this class should be used to send L{Message} and
    L{Bundle}s over the network.
    """

    def __init__(self):
        d = defer.Deferred()
        def listening(proto):
            self.proto = proto
        d.addCallback(listening)
        self._port = reactor.listenUDP(0, OscClientProtocol(d))


    def send(self, element, (host, port)):
        """
        Send a L{Message} or L{Bundle} to the address specified.
        """
        data = element.toBinary()
        self.proto.transport.write(data, (host, port))


    def stop(self):
        return self._port.stopListening()


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
