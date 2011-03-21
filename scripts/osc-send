#!/usr/bin/env python
# Copyright (c) 2009 Alexandre Quessy, Arjan Scherpenisse
# See LICENSE for details.
"""
Sends OSC messages using txosc
"""
import exceptions
import sys
import optparse
import socket
from twisted.internet import reactor
import txosc # for __version__
from txosc import osc
from txosc import dispatch
from txosc import async
from txosc import sync

VERBOSE = False
QUIET = False
RETURN_VALUE = 0

def send_async_udp(message, port, host):
    """
    Sends a message using UDP and stops the Reactor
    @param message: OSC message
    @type message: L{txosc.osc.Message}
    @type port: C{int}
    @type host: C{str}
    """
    client = async.DatagramClientProtocol()
    _client_port = reactor.listenUDP(0, client)
    
    def actually_send_it():
        # verb("Sending %s to %s:%d" % (message, host, port))
        client.send(message, (host, port))
        verb("Sent %s to %s:%d" % (message, host, port))
        reactor.callLater(0.001, reactor.stop)

    reactor.callLater(0, actually_send_it)

def send_sync_tcp(message, port, host):
    try:
        tcp_sender = sync.TcpSender(host, port)
    except socket.error, e:
        print(str(e))
    else:
        tcp_sender.send(message)
        tcp_sender.close()
        verb("Sent %s to %s:%d" % (message, host, port))

def send_sync_udp(message, port, host):
    try:
        udp_sender = sync.UdpSender(host, port)
    except socket.error, e:
        print(str(e))
    else:
        udp_sender.send(message)
        udp_sender.close()
        verb("Sent %s to %s:%d" % (message, host, port))

def send_async_tcp(message, port, host):
    """
    Not yet implemented.
    """
    client = async.ClientFactory()
    _client_port = None
    
    def _callback(result):
        verb("Connected.")
        client.send(message)
        verb("Sent %s to %s:%d" % (message, host, port))
        reactor.callLater(0.001, reactor.stop)

    def _errback(reason):
        print("An error occurred: %s" % (reason.getErrorMessage()))

    _client_port = reactor.connectTCP(host, port, client)
    client.deferred.addCallback(_callback)
    client.deferred.addErrback(_errback)

def create_message_auto(path, *args):
    """
    Trying to guess the type tags.
    """
    message = osc.Message(path)
    for arg in args:
        try:
            value = int(arg)
        except ValueError:
            try:
                value = float(arg)
            except ValueError:
                value = str(arg)
        message.add(value)
    return message

def create_message_manually(path, types, *args):
    """
    The used specified the type tags.
    """
    def _exit_with_error(message):
        global RETURN_VALUE
        if reactor.running:
            reactor.stop()
        print(message)
        RETURN_VALUE = 1 # error
        
    if len(types) != len(args):
        _exit_with_error("The length of the type string must match the number of arguments.")
        return

    message = osc.Message(path)
    try:
        for value, typetag in zip(args, types):
            verb("Creating argument for %s with type tag %s" % (value, typetag))
            cast = str

            if typetag == "i":
                cast = int
            elif typetag == "f":
                cast = float
            elif typetag in ["T", "F"]:
                cast = None
            elif typetag == "t":
                cast = None
            elif typetag == "N":
                cast = None
            elif typetag == "I":
                cast = None
            elif typetag == "":
                cast = None

            if cast is not None:
                try:
                    casted = cast(value)
                except ValueError, e:
                    _exit_with_error("Error converting an argument to type tag" + str(e))
                    return
            else:
                casted = value
            arg = osc.createArgument(casted, typetag)
            verb("Adding argument %s." % (arg))
            message.add(arg)
    except osc.OscError, e:
        _exit_with_error(str(e))
        return None
    return message

def verb(txt):
    """
    Prints a message if in verbose mode.
    """
    global VERBOSE
    if VERBOSE:
        print(txt)

class Config(object):
    def __init__(self):
        self.path = "/"
        self.host = "127.0.0.1"
        self.port = 31337
        self.protocol = "UDP"
        self.type_tags = ""
        self.using_twisted = False

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog [url] /<osc path> [type tags] [arguments values]", version=txosc.__version__.strip(), description=__doc__)
    parser.add_option("-p", "--port", type="int", default=31337, help="Port to send to")
    parser.add_option("-H", "--host", type="string", default="127.0.0.1", help="IP address to send to")
    parser.add_option("-t", "--type-tags", type="string", help="Type tags as many letters concatenated")
    parser.add_option("-v", "--verbose", action="store_true", help="Makes the output verbose")
    parser.add_option("-T", "--tcp", action="store_true", help="Uses TCP instead of UDP")
    parser.add_option("-x", "--enable-twisted", action="store_true", help="Uses Twisted instead of blocking sockets")
    (options, args) = parser.parse_args()

    def _exit(txt):
        """
        Exits right aways - The Twisted reactor must not be running
        """
        print(txt)
        sys.exit(1)

    if len(args) == 0:
        _exit("You must specify an OSC path to send to")

    config = Config()

    config.path = None
    config.host = options.host
    config.port = options.port
    config.protocol = "UDP"
    config.type_tags = options.type_tags
    type_tag_arg_index = 1
    args_index = 1
    url = None
    
    if options.verbose:
        VERBOSE = True
    if options.enable_twisted:
        config.using_twisted = True
        verb("Using Twisted")
    else:
        verb("Using blocking socket networking")
    if options.tcp:
        config.protocol = "TCP"
    if args[0].startswith("/"):
        config.path = args[0]
    elif args[0].startswith("osc."):
        type_tag_arg_index += 1
        args_index += 1
        if len(args) == 1:
            _exit("You must specify an OSC path to send to")
        else:
            if args[1].startswith("/"):
                config.path = args[1]
            url = args[0]
            if url.startswith("osc.udp://"):
                config.protocol = "UDP"
            elif url.startswith("osc.tcp://"):
                config.protocol = "TCP"
            else:
                _exit("The URL must start with either osc.udp or osc.tcp")
            try:
                config.host = url.split("/")[2].split(":")[0]
                config.port = int(url.split(":")[2])
            except IndexError, e:
                _exit(str(e))
            except ValueError, e:
                _exit(str(e))
    
    if len(args) > type_tag_arg_index:
        if args[type_tag_arg_index].startswith(","):
            config.type_tags = args[type_tag_arg_index][1:]
            args_index += 1
    if config.path is None:
        _exit("You must specify an OSC path")
    
    # verb("protocol: %s" % (protocol))
    # verb("host: %s" % (host))
    # verb("port: %s" % (port))
    # verb("path: %s" % (path))
    # verb("type_tags: %s" % (type_tags))
    # verb("type_tag_arg_index: %s" % (type_tag_arg_index))
    # verb("args_index: %s" % (args_index))
        
    def _later():
        # verb("Sending to osc.%s://%s:%d" % (protocol.lower(), host, port))
        if config.type_tags:
            message = create_message_manually(config.path, config.type_tags, *args[args_index:])
        else:
            message = create_message_auto(config.path, *args[args_index:])
        
        if config.using_twisted:
            if config.protocol == 'UDP':
                send_async_udp(message, config.port, config.host)
            else:
                send_async_tcp(message, config.port, config.host)
        else:
            if config.protocol == 'UDP':
                send_sync_udp(message, config.port, config.host)
            else:
                send_sync_tcp(message, config.port, config.host)
        
    if config.using_twisted:
        reactor.callLater(0.001, _later)
        # verb("Starting the Twisted reactor")
        try:
            reactor.run()
        except exceptions.SystemExit:
            pass
    else:
        _later()
    sys.exit(RETURN_VALUE)

