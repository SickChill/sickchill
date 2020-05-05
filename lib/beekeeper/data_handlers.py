"""
This module provides methods to parse various data
types into and out of binary form. Similar way of
doing things to variable_handlers; we map MIME types
to format-specific classes in a dictionary, and then
have a generic "run" method that directs requests
passed to it to the correct format-specific method.
"""

from __future__ import absolute_import, division
from __future__ import unicode_literals, print_function

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import json
import json.decoder
from functools import partial

import xmltodict

class DataHandlerMeta(type):

    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            cls.registry = {}
        else:
            cls.registry.update(**{mimetype: cls for mimetype in dct.get('mimetypes', [dct.get('mimetype')])})
        super(DataHandlerMeta, cls).__init__(name, bases, dct)

DataHandler = DataHandlerMeta(str('DataHandler'), (object,), {})

class XMLParser(DataHandler):
    mimetypes = ['application/xml', 'text/xml']

    @staticmethod
    def dump(python_object, encoding):
        if python_object:
            return xmltodict.unparse(python_object).encode(encoding)

    @staticmethod
    def load(response, encoding):
        return xmltodict.parse(response, encoding=encoding, xml_attribs=True, dict_constructor=dict)

class JSONParser(DataHandler):
    mimetype = 'application/json'

    @staticmethod
    def dump(python_object, encoding):
        if python_object:
            return json.dumps(python_object).encode(encoding)

    @staticmethod
    def load(response, encoding):
        return json.loads(response.decode(encoding))

class HTTPFormEncoder(DataHandler):
    mimetype = 'application/x-www-form-urlencoded'

    @staticmethod
    def dump(python_object, encoding):
        if python_object:
            return urlencode(python_object).encode(encoding)

class PlainText(DataHandler):
    mimetypes = ['text/plain', 'text/html']

    @staticmethod
    def dump(python_object, encoding):
        if python_object:
            return str(python_object).encode(encoding)

    @staticmethod
    def load(response, encoding):
        response = response.decode(encoding)
        try:
            return json.loads(response)
        except ValueError:
            return response
        except json.decoder.JSONDecodeError:
            return response

class Binary(DataHandler):
    mimetypes = ['application/octet-stream']

    @staticmethod
    def dump(python_object, encoding):
        if python_object:
            return python_object

    @staticmethod
    def load(response, encoding):
        return response

def code(action, data, mimetype, encoding='utf-8'):
    if action == 'dump' and hasattr(data, 'read'):
        data = data.read()
    if action == 'dump' and isinstance(data, bytes):
        return getattr(Binary, action)(data, encoding)
    if action == 'load' and not data:
        return None
    if action == 'load' and mimetype not in DataHandler.registry:
        return getattr(Binary, action)(data, encoding)
    if mimetype in DataHandler.registry and getattr(DataHandler.registry[mimetype], action, None):
        return getattr(DataHandler.registry[mimetype], action)(data, encoding)
    else:
        raise Exception('Cannot parse MIME type {}'.format(mimetype))

encode = partial(code, 'dump')
decode = partial(code, 'load')
