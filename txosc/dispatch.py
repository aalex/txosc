#!/usr/bin/env python
# -*- test-case-name: txosc.test.test_dispatch -*-
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.

"""
OSC message address dispatching to callbacks
"""
import string
import math
import struct
import re
from txosc.osc import *

class AddressNode(object):
    """
    A node in the tree of OSC addresses.
    
    This node can be either a container branch or a leaf. An OSC address is a series of names separated by forward slash characters. ('/') We say that a node is a branch when it has one or more child nodes. 

    This class is provided so that the programmer can separate the handling of an address sub-tree in the OSC addresses. For example, an AddressNode can be added to a receiver in order to handle all the messages starting with "/egg/spam/". AddressNode classes can be nested.

    @ivar _name: the name of this node. 
    @ivar _parent: the parent node.
    """

    def __init__(self, name=None, parent=None):
        """
        @type name: C{str}
        @param parent: L{Receiver} or L{AddressNode}
        """
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
        @type newname: C{str}
        """
        if self._parent:
            del self._parent._childNodes[self._name]
        self._name = newname
        if self._parent:
            self._parent._childNodes[self._name] = self


    def setParent(self, newparent):
        """
        Reparent this node to another parent.
        @param newparent: L{Receiver} or L{AddressNode}
        """
        if self._parent:
            del self._parent._childNodes[self._name]
            self._parent._checkRemove()
        self._parent = newparent
        self._parent._childNodes[self._name] = self

#    def getParent(self):
#        """
#        Returns the parent node or None.
#        """
#        return self._parent
#    
#    def getChildren(self):
#        """
#        Returns a set of children nodes.
#        """
#        return set(self._childNodes)
        


    def _checkRemove(self):
        if not self._parent:
            return
        if not self._callbacks and not self._childNodes:
            del self._parent._childNodes[self._name]
        self._parent._checkRemove()


    def addNode(self, name, instance):
        """
        Add a child node.
        @type name: C{str}
        @type instance: L{AddressNode}
        """
        #FIXME: We should document the name. 
        # Is it /foo or foo?
        # Does it redirect all messages prefixed with "/foo" to the child?
        instance.setName(name)
        instance.setParent(self)


    def getName(self):
        """
        Returns the name of this address node.
        """
        return self._name


    def match(self, pattern):
        """
        Match a pattern to return a set of nodes.

        @param pattern: A C{str} with an address pattern.
        @return a C{set()} of matched AddressNode instances.
        """

        path = self._patternPath(pattern)
        if not len(path):
            return set([self])

        matchedNodes = set()

        part = path[0]
        if AddressNode.isWildcard(part):
            for c in self._childNodes:
                if AddressNode.matchesWildcard(c, part):
                    matchedNodes.add( self._childNodes[c] )
            # FIXME - what if both the part and some of my childs have wildcards?
        elif self._wildcardNodes:
            matches = set()
            for c in self._wildcardNodes:
                if AddressNode.matchesWildcard(part, c):
                    matchedNodes.add( self._childNodes[c] )
                    break
        if part in self._childNodes:
            matchedNodes.add( self._childNodes[part] )

        if not matchedNodes:
            return matchedNodes
        return reduce(lambda a, b: a.union(b), [n.match(path[1:]) for n in matchedNodes])


    def addCallback(self, pattern, cb):
        """
        Adds a callback for L{txosc.osc.Message} instances received for a given OSC path, relative to this node's address as its root. 

        In the OSC protocol, only leaf nodes can have callbacks, though this implementation allows also branch nodes to have callbacks.

        @param path: OSC address in the form C{/egg/spam/ham}, or list C{['egg', 'spam', 'ham']}.
        @type pattern: C{str} or C{list}.
        @param cb: Callback that will receive L{Message} as an argument when received.
        @type cb: Function or method.
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
        @param cb: Callback that will receive L{txosc.osc.Message} as an argument when received.
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

        wildcard = wildcard.replace("*", ".*")
        wildcard = wildcard.replace("?", ".?")
        wildcard = wildcard.replace("[!", "[^")
        wildcard = wildcard.replace("(", "\(")
        wildcard = wildcard.replace(")", "\)")
        wildcard = wildcard.replace("|", "\|")
        wildcard = wildcard.replace("{", "(")
        wildcard = wildcard.replace("}", ")")
        wildcard = wildcard.replace(",", "|")
        wildcard = "^" + wildcard + "$"

        try:
            r = re.compile(wildcard)
            return re.match(wildcard, value) is not None
        except:
            raise OscError("Invalid character in wildcard.")


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


    def removeCallbacksByPattern(self, pattern):
        """
        Remove all callbacks with the given pattern.

        @param pattern: The pattern to match the callbacks. When
        ommited, removes all callbacks.
        """
        raise NotImplementedError("Implement removeCallbacks")

    def removeAllCallbacks(self):
        """
        Remove all callbacks from this node.
        """
        self._childNodes = {}
        self._wildcardNodes = set()
        self._callbacks = set()
        self._checkRemove()


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

    def dispatch(self, element, client):
        """
        Dispatch an element to all matching callbacks.

        Executes every callback matching the message address with
        element as argument. The order in which the callbacks are
        called is undefined.

        @param element: A L{Message} or L{Bundle}.  
        @param client: Either a (host, port) tuple with the originator's address, or an instance of L{StreamBasedFactory} whose C{send()} method can be used to send a message back.
        """
        if isinstance(element, Bundle):
            messages = element.getMessages()
        else:
            messages = [element]
        for m in messages:
            matched = False
            for c in self.getCallbacks(m.address):
                c(m, client)
                matched = True
            if not matched:
                self.fallback(m, client)

    #TODO: add a addFallback or setFallback method
    def fallback(self, message, client):
        """
        The default fallback handler.
        """
        from twisted.python import log
        log.msg("Unhandled message from %s): %s" % (repr(client), str(message)))

    def setFallback(self, fallback):
        """
        Sets the fallback.
        @param fallback: callable function or method.
        """
        self.fallback = fallback
