""" JSON Web Token implementation

Minimum implementation based on this spec:
http://self-issued.info/docs/draft-jones-json-web-token-01.html
"""
import base64
import hashlib
import hmac
from six import text_type, b


# default text to binary representation conversion
def binary(txt):
    return txt.encode('utf-8')

try:
    import json
except ImportError:
    import simplejson as json


__all__ = ['encode', 'decode', 'DecodeError']


class DecodeError(Exception):
    pass

signing_methods = {
    'HS256': lambda msg, key: hmac.new(key, msg, hashlib.sha256).digest(),
    'HS384': lambda msg, key: hmac.new(key, msg, hashlib.sha384).digest(),
    'HS512': lambda msg, key: hmac.new(key, msg, hashlib.sha512).digest(),
}


def base64url_decode(input):
    input += b('=') * (4 - (len(input) % 4))
    return base64.urlsafe_b64decode(input)


def base64url_encode(input):
    return base64.urlsafe_b64encode(input).decode('utf-8').replace('=', '')


def encode(payload, key, algorithm='HS256', headers=None):
    segments = []
    header = {"typ": "JWT", "alg": algorithm}
    if headers:
        header.update(headers)
    segments.append(base64url_encode(binary(json.dumps(header))))
    segments.append(base64url_encode(binary(json.dumps(payload))))
    sign_input = '.'.join(segments)
    try:
        signature = signing_methods[algorithm](binary(sign_input), binary(key))
    except KeyError:
        raise NotImplementedError("Algorithm not supported")
    segments.append(base64url_encode(signature))
    return '.'.join(segments)


def decode(jwt, key='', verify=True):
    try:
        signing_input, crypto_segment = jwt.rsplit('.', 1)
        header_segment, payload_segment = signing_input.split('.', 1)
    except ValueError:
        raise DecodeError("Not enough segments")
    try:
        header_raw = base64url_decode(binary(header_segment)).decode('utf-8')
        payload_raw = base64url_decode(binary(payload_segment)).decode('utf-8')
        header = json.loads(header_raw)
        payload = json.loads(payload_raw)
        signature = base64url_decode(binary(crypto_segment))
    except (ValueError, TypeError):
        raise DecodeError("Invalid segment encoding")
    if verify:
        try:
            method = signing_methods[header['alg']]
            if not signature == method(binary(signing_input), binary(key)):
                raise DecodeError("Signature verification failed")
        except KeyError:
            raise DecodeError("Algorithm not supported")
    return payload
