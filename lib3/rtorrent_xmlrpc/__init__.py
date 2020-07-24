#!/usr/bin/env python3

# rtorrent_xmlrpc
# (c) 2011 Roger Que <alerante@bellsouth.net>
# Updated for python3 by Daniel Bowring <contact@danielb.codes>
#
# Python module for interacting with rtorrent's XML-RPC interface
# directly over SCGI, instead of through an HTTP server intermediary.
# Inspired by Glenn Washburn's xmlrpc2scgi.py [1], but subclasses the
# built-in xmlrpclib classes so that it is compatible with features
# such as MultiCall objects.
#
# [1] <http://libtorrent.rakshasa.no/wiki/UtilsXmlrpc2scgi>
#

import socket
import string
import collections
import xmlrpc.client



__all__ = [
    'SCGITransport',
    'SCGIServerProxy'
]

NULL = b'\x00'


class SCGITransport(xmlrpc.client.Transport):
    def encode_scgi_headers(self, content_length, **others):
        # Need to use an ordered dict because content length MUST be the first
        #  key present in the encoded headers.
        headers = collections.OrderedDict((
            (b'CONTENT_LENGTH', str(content_length).encode('utf-8')),
            (b'SCGI', b'1'),
        ))
        headers.update(others)  # Assume already bytes for keys and values

        encoded = NULL.join( k + NULL + v for k, v in headers.items() ) + NULL
        length = str(len(encoded)).encode('utf-8')
        return length + b':' + encoded


    def single_request(self, host, handler, request_body, verbose=0):
        # Add SCGI headers to the request.
        header = self.encode_scgi_headers(len(request_body))
        scgi_request = header + b',' + request_body

        sock = None

        try:
            if host:
                host, port = splitport(host)
                addrinfo = socket.getaddrinfo(host, port, socket.AF_INET,
                                              socket.SOCK_STREAM)
                sock = socket.socket(*addrinfo[0][:3])
                sock.connect(addrinfo[0][4])
            else:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(handler)

            self.verbose = verbose

            sock.send(scgi_request)
            return self.parse_response(sock.makefile())
        finally:
            if sock:
                sock.close()

    def response_split_header(self, response):
        try:
            index = response.index('\n')
            while not response[index+1] in string.whitespace:
                index = response.index('\n', index+1)

        except (ValueError, IndexError) as e:
            msg = 'Unable to split response into header and body sections'
            raise ValueError(msg) from e

        offset = 2  # Know at least the following character is whitespace
        try:
            while response[index+offset] in string.whitespace:
                offset + 1
        except IndexError:
            return response, ''  # Reached the end - there is no body

        # Split by and remove the whitespace
        return response[:index], response[index+offset:]

    def parse_response(self, response):
        p, u = self.getparser()

        response_body = ''
        while True:
            data = response.read(1024)
            if not data:
                break
            response_body += data

        # Remove SCGI headers from the response.
        response_header, response_body = self.response_split_header(response_body)

        if self.verbose:
            print('body:', repr(response_body))

        p.feed(response_body)
        p.close()

        return u.close()


class SCGIServerProxy(xmlrpc.client.ServerProxy):
    def __init__(self, uri, transport=None, use_datetime=False,
                 use_builtin_types=False, **kwargs):

        scheme, uri = splittype(uri)

        if scheme != 'scgi':
            raise IOError('unsupported XML-RPC protocol')

        if transport is None:
            transport = SCGITransport(use_datetime=use_datetime,
                                      use_builtin_types=use_builtin_types)

        # Feed some junk in here, but we'll fix it afterwards
        super().__init__('http://thiswillbe/overwritten', transport=transport, **kwargs)

        # Fix the result of the junk above
        # The names are weird here because of name mangling. See:
        #  https://docs.python.org/3/tutorial/classes.html#private-variables
        self._ServerProxy__host, self._ServerProxy__handler = splithost(uri)

        if not self._ServerProxy__handler:
            self._ServerProxy__handler = '/'


def splittype(url):
    '''
    splittype('type:opaquestring') --> 'type', 'opaquestring'.

    If type is unknown, it will be `None`. Type will always be returned
     in lowercase.
    This functionality use to (sort of) be provided by urllib as
     `urllib.splittype` in python2, but has since been removed.
    '''
    try:
        split_at = url.index(':')
    except ValueError:
        return None, url  # Can't tell what the type is

    # Don't include the colon in either value.
    return url[:split_at].lower(), url[split_at+1:]


def splithost(url):
    '''
    splithost('//host[:port]/path') --> 'host[:port]', '/path'.

    This functionality use to (sort of) be provided by urllib as
     `urllib.splithost` in python2, but has since been removed.
    '''

    if not url.startswith('//'):
        return None, url  # Probably a relative path

    hostpath = url[2:]  # remove the '//'

    try:
        split_from = hostpath.index('/')
    except ValueError:
        return url, None  # Seems to contain host only

    # Unlike `splittype`, we want the separating character in the path
    return hostpath[:split_from], hostpath[split_from:]


def is_non_digit(character):
    return not character in string.digits

def splitport(hostport):
    '''
    splitport('host:port') --> 'host', 'port'.

    This functionality use to (sort of) be provided by urllib as
     `urllib.splithost` in python2, but has since been removed.
    '''

    try:
        host, port = hostport.split(':', 1)  # ValueError if there is no colon
    except ValueError:
        return hostport, None

    # Port should contain only digits
    if any(map(is_non_digit, port)):
        return hostport, None

    return host, port


