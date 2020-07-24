import base64
import hmac
from hashlib import sha1, sha256

from six import PY3, string_types

from twilio.compat import izip, urlparse, parse_qs


def compare(string1, string2):
    """Compare two strings while protecting against timing attacks

    :param str string1: the first string
    :param str string2: the second string

    :returns: True if the strings are equal, False if not
    :rtype: :obj:`bool`
    """
    if len(string1) != len(string2):
        return False
    result = True
    for c1, c2 in izip(string1, string2):
        result &= c1 == c2

    return result


def remove_port(uri):
    """Remove the port number from a URI

    :param uri: parsed URI that Twilio requested on your server

    :returns: full URI without a port number
    :rtype: str
    """
    if not uri.port:
        return uri.geturl()

    new_netloc = uri.netloc.split(':')[0]
    new_uri = uri._replace(netloc=new_netloc)

    return new_uri.geturl()


def add_port(uri):
    """Add the port number to a URI

    :param uri: parsed URI that Twilio requested on your server

    :returns: full URI with a port number
    :rtype: str
    """
    if uri.port:
        return uri.geturl()

    port = 443 if uri.scheme == "https" else 80
    new_netloc = uri.netloc + ":" + str(port)
    new_uri = uri._replace(netloc=new_netloc)

    return new_uri.geturl()


class RequestValidator(object):

    def __init__(self, token):
        self.token = token.encode("utf-8")

    def compute_signature(self, uri, params, utf=PY3):
        """Compute the signature for a given request

        :param uri: full URI that Twilio requested on your server
        :param params: post vars that Twilio sent with the request
        :param utf: whether return should be bytestring or unicode (python3)

        :returns: The computed signature
        """
        s = uri
        if params:
            for k, v in sorted(params.items()):
                s += k + v

        # compute signature and compare signatures
        mac = hmac.new(self.token, s.encode("utf-8"), sha1)
        computed = base64.b64encode(mac.digest())
        if utf:
            computed = computed.decode('utf-8')

        return computed.strip()

    def compute_hash(self, body):
        computed = sha256(body.encode("utf-8")).hexdigest()

        return computed.strip()

    def validate(self, uri, params, signature):
        """Validate a request from Twilio

        :param uri: full URI that Twilio requested on your server
        :param params: dictionary of POST variables or string of POST body for JSON requests
        :param signature: expected signature in HTTP X-Twilio-Signature header

        :returns: True if the request passes validation, False if not
        """
        if params is None:
            params = {}

        parsed_uri = urlparse(uri)
        uri_with_port = add_port(parsed_uri)
        uri_without_port = remove_port(parsed_uri)

        valid_signature = False  # Default fail
        valid_signature_with_port = False
        valid_body_hash = True  # May not receive body hash, so default succeed

        query = parse_qs(parsed_uri.query)
        if "bodySHA256" in query and isinstance(params, string_types):
            valid_body_hash = compare(self.compute_hash(params), query["bodySHA256"][0])
            params = {}

        #  check signature of uri with and without port,
        #  since sig generation on back end is inconsistent
        valid_signature = compare(self.compute_signature(uri_without_port, params), signature)
        valid_signature_with_port = compare(self.compute_signature(uri_with_port, params), signature)

        return valid_body_hash and (valid_signature or valid_signature_with_port)
