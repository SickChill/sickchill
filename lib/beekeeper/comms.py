"""
Provides classes and methods related to communicating with the remote API
"""

from __future__ import absolute_import, division
from __future__ import unicode_literals, print_function

try:
    from urllib2 import Request as Py2Request, HTTPError, URLError
    from urllib2 import build_opener, HTTPCookieProcessor
    from urllib import urlencode
    import httplib
    import cookielib
    pyversion = 2

except ImportError:
    from urllib.request import Request as PythonRequest, build_opener
    from urllib.request import HTTPCookieProcessor
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    import http.client as httplib
    import http.cookiejar as cookielib
    pyversion = 3

import socket
import functools

from beekeeper.variable_handlers import render
from beekeeper.data_handlers import decode
from beekeeper.exceptions import TraversalError, TooMuchBodyData, RequestTimeout

if pyversion == 2:
    class PythonRequest(Py2Request):

        def __init__(self, *args, **kwargs):
            self._method = kwargs.pop('method', None)
            Py2Request.__init__(self, *args, **kwargs)

        def get_method(self):
            return self._method if self._method else super(PythonRequest, self).get_method()
elif pyversion == 3:
    basestring = str


COOKIE_JAR = cookielib.CookieJar()
REQUEST_OPENER = build_opener(HTTPCookieProcessor(COOKIE_JAR))

def download_as_json(url):
    """
    Download the data at the URL and load it as JSON
    """
    try:
        return Response('application/json', request(url=url)).read()
    except HTTPError as err:
        raise ResponseException('application/json', err)

def request(*args, **kwargs):
    """
    Make a request with the received arguments and return an
    HTTPResponse object
    """
    timeout = kwargs.pop('timeout', 5)
    req = PythonRequest(*args, **kwargs)
    return REQUEST_OPENER.open(req, timeout=timeout)

class Request(object):

    """
    Holds data and provides methods related to building and sending
    an HTTP request with the data passed to it
    """

    def __init__(self, action, variables):
        self.action = action
        self.url = self.action.endpoint.url()
        self.replacements = {}
        self.params = {}
        self.output = {
            'data': None,
            'headers': {},
            'method': self.action.method
        }
        for var_type in variables.types():
            render(self, var_type, **variables.vals(var_type))

    def send(self, **kwargs):
        """
        Send the request defined by the data stored in the object.
        """
        return_full_object = kwargs.get('return_full_object', False)
        _verbose = kwargs.get('_verbose', False)
        traversal = kwargs.get('traversal', None)
        timeout = kwargs.get('_timeout', 5)
        self.output['url'] = self.render_url()
        with VerboseContextManager(verbose=_verbose):
            try:
                resp = Response(self.action.format(), request(timeout=timeout, **self.output), traversal)
            except HTTPError as err:
                raise ResponseException(self.action.format(), err)
            except URLError as err:
                if isinstance(err.reason, socket.timeout):
                    raise RequestTimeout(functools.partial(self.send, **kwargs))
                else:
                    raise

        if return_full_object:
            return resp
        else:
            return resp.read()

    def set_headers(self, **headers):
        self.output['headers'].update(headers)

    def set_data(self, data, override=False):
        if self.output['data'] is None or override:
            self.output['data'] = data
        else:
            raise TooMuchBodyData(self.output['data'], data)

    def set_url_params(self, **params):
        self.params.update(params)

    def set_url_replacements(self, **replacements):
        self.replacements.update(replacements)

    def render_url(self):
        """
        Render the final URL based on available variables
        """
        url = self.url.format(**self.replacements)
        if self.params:
            return url + '?' + urlencode(self.params)
        return url

class Response(object):

    """
    Stores data and provides methods related to the response that
    we get back from the API provider's server
    """

    def __init__(self, static_format, response, traversal=None):
        self.static_format = static_format
        self.headers = response.headers
        self.data = response.read()
        self.code = response.getcode()
        self.message = response.msg
        self.traversal = traversal

    def mimetype(self):
        """
        Get the Content-Type header from the response. Strip
        the ";charset=xxxxx" portion if necessary. If we can't
        find it, use the predefined format.
        """
        if ';' in self.headers.get('Content-Type', ''):
            return self.headers['Content-Type'].split(';')[0]
        return self.headers.get('Content-Type', self.static_format)

    def encoding(self):
        """
        Look for a "charset=" variable in the Content-Type header;
        if it's not there, just return a default value of UTF-8
        """
        if 'charset=' in self.headers.get('Content-Type', ''):
            return self.headers['Content-Type'].split('charset=')[1].split(';')[0]
        return 'utf-8'

    def read(self, raw=False, perform_traversal=True):
        """
        Parse the body of the response using the Content-Type
        header we pulled from the response, or the hive-defined
        format, if such couldn't be pulled automatically.
        """
        if not raw:
            response_body = decode(self.data, self.mimetype(), encoding=self.encoding())
            if perform_traversal and self.traversal is not None:
                return traverse(response_body, *self.traversal)
            return response_body
        else:
            return self.data

def traverse(obj, *path, **kwargs):
    """
    Traverse the object we receive with the given path. Path
    items can be either strings or lists of strings (or any
    nested combination thereof). Behavior in given cases is
    laid out line by line below.
    """
    if path:
        if isinstance(obj, list) or isinstance(obj, tuple):
            #If the current state of the object received is a
            #list, return a list of each of its children elements,
            #traversed with the current state of the string
            return [traverse(x, *path) for x in obj]
        elif isinstance(obj, dict):
            #If the current state of the object received is a
            #dictionary, do the following...
            if isinstance(path[0], list) or isinstance(path[0], tuple):
                #If the current top item in the path is a list,
                #return a dictionary with keys to each of the
                #items in the list, each traversed recursively.
                for branch in path[0]:
                    if not isinstance(branch, basestring):
                        raise TraversalError(obj, path[0])
                return {name: traverse(obj[name], *path[1:], split=True) for name in path[0]}
            elif not isinstance(path[0], basestring):
                #If the key isn't a string (or a list; handled
                #previously), raise an exception.
                raise TraversalError(obj, path[0])
            elif path[0] == '\\*':
                #If the key is a wildcard, return a dict containing
                #each item, traversed down recursively.
                return {name: traverse(item, *path[1:], split=True) for name, item in obj.items()}
            elif path[0] in obj:
                #The individual key is in the current object;
                #traverse it and return the result.
                return traverse(obj[path[0]], *path[1:])
            else:
                #The individual key doesn't exist in the
                #current object; raise an error
                raise TraversalError(obj, path[0])
        else:
            #If the current object isn't either a list or
            #a dict, then do one of two things:
            if kwargs.get('split', False):
                #If the previously-recursed operation caused
                #a split in a dict, just return the object; it's
                #been specifically called out, but it isn't
                #possible to recurse further.
                return obj
            else:
                #The object can't be traversed, and we didn't
                #specifically call it out to do something
                #else with. Raise an exception.
                raise TraversalError(obj, path[0])
    else:
        #If there's no path left, then just return the
        #object that we received.
        return obj

class ResponseException(Response, Exception):
    """
    The exception we raise when we get an HTTPError back from
    the remote server. It's here and not in beekeeper.exceptions
    because it inherits from Response, and we need to avoid
    circular dependencies.
    """

    def __init__(self, static_format, response):
        Response.__init__(self, static_format, response, traversal=None)

    def __str__(self):
        return 'Error message: {}/{}'.format(self.code, self.message)

class VerboseContextManager(object):
    """
    Sets httplib to verbose on __enter__; returns it to its
    previous state on __exit__.
    """

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.previous_state = httplib.HTTPConnection.debuglevel

    def __enter__(self):
        if self.verbose:
            httplib.HTTPConnection.debuglevel = 1

    def __exit__(self, *args, **kwargs):
        httplib.HTTPConnection.debuglevel = self.previous_state
