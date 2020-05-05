"""
This module provides methods that parse variables into
one of the three base level variable types. We map the
variable type names to methods that can handle them. Each
method consumes a Request object 'rq' as the first positional
argument, and does its work by calling one of the variable-setting
methods on rq.
"""

from __future__ import absolute_import, division
from __future__ import unicode_literals, print_function

from uuid import uuid4
from functools import partial
from base64 import b64encode

from beekeeper.data_handlers import encode
from beekeeper.exceptions import CannotHandleVariableTypes

class VariableHandler(object):

    registry = {}

    def __init__(self, *var_types):
        self.var_types = var_types

    def __call__(self, func):
        def wrapped(rq, **values):
            return func(rq, **values)
        for each in self.var_types:
            VariableHandler.registry[each] = wrapped
        return wrapped

def identity(**values):
    return {name: val['value'] for name, val in values.items()}

def set_content_type(rq, mimetype):
    rq.set_headers(**{'Content-Type': mimetype})

@VariableHandler('data')
def render_data(rq, **data):
    for val in data.values():
        set_content_type(rq, val['mimetype'])
        rq.set_data(encode(val['value'], val['mimetype']))

@VariableHandler('http_form')
def http_form(rq, **values):
    form = {
        'x': {
            'mimetype': 'application/x-www-form-urlencoded',
            'value': {
                name: val['value'] for name, val in values.items()
            }
        }
    }
    render(rq, 'data', **form)

@VariableHandler('http_basic_auth')
def basic_auth(rq, **values):
    username = values.get('username', {}).get('value', '')
    password = values.get('password', {}).get('value', '')
    authinfo = b64encode("{}:{}".format(username, password).encode('utf-8'))
    authinfo = 'Basic {}'.format(authinfo.decode('utf-8'))
    rq.set_headers(Authorization=authinfo)

@VariableHandler('bearer_token')
def bearer(rq, **values):
    if len(values) > 1:
        raise Exception('Only one bearer token allowed')
    else:
        for token in values.values():
            text = 'Bearer {}'.format(token['value'])
            rq.set_headers(Authorization=text)

@VariableHandler('cookie')
def cookies(rq, **values):
    cookie = '; '.join([value['value'] for value in values.values()])
    rq.set_headers(Cookie=cookie)

@VariableHandler('multipart')
def multipart(rq, **values):
    frame = '\n--{}\nContent-Disposition: form-data; name="{}"'
    boundary = uuid4().hex
    files = [name for name, data in values.items() if 'mimetype' in data]
    output = bytes()
    for name, value in values.items():
        if name in files:
            fname = value.get('filename', getattr(value['value'], 'name', uuid4().hex))
            this_frame = frame + '; filename="{}"\nContent-Type: {}\n\n'
            this_data = encode(value['value'], value['mimetype'])
            args = (boundary, name, fname, value['mimetype'])
        else:
            this_frame = frame + '\n\n'
            this_data = value['value'].encode('ascii')
            args = (boundary, name)
        output += this_frame.format(*args).encode('ascii') + this_data
    output += '\n--{}--'.format(boundary).encode('ascii')
    rq.set_data(output)
    content_type_header = 'multipart/form-data; boundary={}'.format(boundary)
    set_content_type(rq, content_type_header)

@VariableHandler('header')
def header(rq, **values):
    rq.set_headers(**identity(**values))

@VariableHandler('url_replacement')
def replacement(rq, **values):
    rq.set_url_replacements(**identity(**values))

@VariableHandler('url_param')
def url_param(rq, **values):
    rq.set_url_params(**identity(**values))

def render(rq, var_type, **values):
    if var_type in VariableHandler.registry:
        variables = {val.pop('name', name): val for name, val in values.items()}
        VariableHandler.registry[var_type](rq, **variables)
    else:
        raise CannotHandleVariableTypes(var_type)
