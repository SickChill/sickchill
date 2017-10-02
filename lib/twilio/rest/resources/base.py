import logging
import os
import platform

from six import (
    integer_types,
    string_types,
    binary_type,
    iteritems
)
from ...compat import urlencode
from ...compat import urlparse
from ...compat import urlunparse

from ... import __version__
from ...exceptions import TwilioException
from ..exceptions import TwilioRestException
from .connection import Connection
from .imports import parse_qs, httplib2, json
from .util import (
    parse_iso_date,
    parse_rfc2822_date,
    transform_params,
    UNSET_TIMEOUT,
)

logger = logging.getLogger('twilio')


class Response(object):
    """
    Take a httplib2 response and turn it into a requests response
    """
    def __init__(self, httplib_resp, content, url):
        self.content = content
        self.cached = False
        self.status_code = int(httplib_resp.status)
        self.ok = self.status_code < 400
        self.url = url


def get_cert_file():
    """ Get the cert file location or bail """
    # XXX - this currently fails test coverage because we don't actually go
    # over the network anywhere. Might be good to have a test that stands up a
    # local server and authenticates against it.
    try:
        # Apparently __file__ is not available in all places so wrapping this
        # in a try/catch
        current_path = os.path.realpath(__file__)
        ca_cert_path = os.path.join(current_path, "..", "..", "..",
                                    "conf", "cacert.pem")
        return os.path.abspath(ca_cert_path)
    except Exception:
        # None means use the default system file
        return None


def make_request(method, url, params=None, data=None, headers=None,
                 cookies=None, files=None, auth=None, timeout=None,
                 allow_redirects=False, proxies=None):
    """Sends an HTTP request

    :param str method: The HTTP method to use
    :param str url: The URL to request
    :param dict params: Query parameters to append to the URL
    :param dict data: Parameters to go in the body of the HTTP request
    :param dict headers: HTTP Headers to send with the request
    :param float timeout: Socket/Read timeout for the request

    :return: An http response
    :rtype: A :class:`Response <models.Response>` object

    See the requests documentation for explanation of all these parameters

    Currently proxies, files, and cookies are all ignored
    """
    http = httplib2.Http(
        timeout=timeout,
        ca_certs=get_cert_file(),
        proxy_info=Connection.proxy_info(),
    )
    http.follow_redirects = allow_redirects

    if auth is not None:
        http.add_credentials(auth[0], auth[1])

    def encode_atom(atom):
            if isinstance(atom, (integer_types, binary_type)):
                return atom
            elif isinstance(atom, string_types):
                return atom.encode('utf-8')
            else:
                raise ValueError('list elements should be an integer, '
                                 'binary, or string')

    if data is not None:
        udata = {}
        for k, v in iteritems(data):
            key = k.encode('utf-8')
            if isinstance(v, (list, tuple, set)):
                udata[key] = [encode_atom(x) for x in v]
            elif isinstance(v, (integer_types, binary_type, string_types)):
                udata[key] = encode_atom(v)
            else:
                raise ValueError('data should be an integer, '
                                 'binary, or string, or sequence ')
        data = urlencode(udata, doseq=True)

    if params is not None:
        enc_params = urlencode(params, doseq=True)
        if urlparse(url).query:
            url = '%s&%s' % (url, enc_params)
        else:
            url = '%s?%s' % (url, enc_params)

    resp, content = http.request(url, method, headers=headers, body=data)

    # Format httplib2 request as requests object
    return Response(resp, content.decode('utf-8'), url)


def make_twilio_request(method, uri, **kwargs):
    """
    Make a request to Twilio. Throws an error

    :return: a requests-like HTTP response
    :rtype: :class:`RequestsResponse`
    :raises TwilioRestException: if the response is a 400
        or 500-level response.
    """
    headers = kwargs.get("headers", {})

    user_agent = "twilio-python/%s (Python %s)" % (
        __version__,
        platform.python_version(),
    )
    headers["User-Agent"] = user_agent
    headers["Accept-Charset"] = "utf-8"

    if method == "POST" and "Content-Type" not in headers:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    kwargs["headers"] = headers

    if "Accept" not in headers:
        headers["Accept"] = "application/json"

    if kwargs.pop('use_json_extension', False):
        uri += ".json"

    resp = make_request(method, uri, **kwargs)

    if not resp.ok:
        try:
            error = json.loads(resp.content)
            code = error["code"]
            message = error["message"]
        except:
            code = None
            message = resp.content

        raise TwilioRestException(status=resp.status_code, method=method,
                                  uri=resp.url, msg=message, code=code)

    return resp


class Resource(object):
    """A REST Resource"""

    name = "Resource"
    use_json_extension = False

    def __init__(self, base_uri, auth, timeout=UNSET_TIMEOUT):
        self.base_uri = base_uri
        self.auth = auth
        self.timeout = timeout

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __hash__(self):
        return hash(frozenset(self.__dict__))

    def __ne__(self, other):
        return not self.__eq__(other)

    def request(self, method, uri, **kwargs):
        """
        Send an HTTP request to the resource.

        :raises: a :exc:`~twilio.TwilioRestException`
        """
        if 'timeout' not in kwargs and self.timeout is not UNSET_TIMEOUT:
            kwargs['timeout'] = self.timeout

        kwargs['use_json_extension'] = self.use_json_extension
        resp = make_twilio_request(method, uri, auth=self.auth, **kwargs)

        logger.debug(resp.content)

        if method == "DELETE":
            return resp, {}
        else:
            return resp, json.loads(resp.content)

    @property
    def uri(self):
        format = (self.base_uri, self.name)
        return "%s/%s" % format


class InstanceResource(Resource):
    """ The object representation of an instance response from the Twilio API

    :param parent: The parent list class for this instance resource.
        For example, the parent for a :class:`~twilio.rest.resources.Call`
        would be a :class:`~twilio.rest.resources.Calls` object.
    :type parent: :class:`~twilio.rest.resources.ListResource`
    :param str sid: The 34-character unique identifier for this instance
    """

    subresources = []
    id_key = "sid"
    use_json_extension = True

    def __init__(self, parent, sid):
        self.parent = parent
        self.name = sid
        super(InstanceResource, self).__init__(
            parent.uri,
            parent.auth,
            parent.timeout
        )

    def load(self, entries):
        if "from" in entries.keys():
            entries["from_"] = entries["from"]
            del entries["from"]

        if "uri" in entries.keys():
            del entries["uri"]

        for key in entries.keys():
            if (key.startswith("date_") and
                    isinstance(entries[key], string_types)):
                entries[key] = self._parse_date(entries[key])

        self.__dict__.update(entries)

    def load_subresources(self):
        """
        Load all subresources
        """
        for resource in self.subresources:
            list_resource = resource(
                self.uri,
                self.parent.auth,
                self.parent.timeout
            )
            self.__dict__[list_resource.key] = list_resource

    def update_instance(self, **kwargs):
        """ Make a POST request to the API to update an object's properties

        :return: None, this is purely side effecting
        :raises: a :class:`~twilio.rest.RestException` on failure
        """
        a = self.parent.update(self.name, **kwargs)
        self.load(a.__dict__)

    def delete_instance(self):
        """ Make a DELETE request to the API to delete the object

        :return: None, this is purely side effecting
        :raises: a :class:`~twilio.rest.RestException` on failure
        """
        return self.parent.delete(self.name)

    def _parse_date(self, s):
        return parse_rfc2822_date(s)

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name[0:5])


class NextGenInstanceResource(InstanceResource):

    use_json_extension = False

    def __init__(self, *args, **kwargs):
        super(NextGenInstanceResource, self).__init__(*args, **kwargs)

    def _parse_date(self, s):
        return parse_iso_date(s)


class ListResource(Resource):

    name = "Resources"
    instance = InstanceResource
    use_json_extension = True

    def __init__(self, *args, **kwargs):
        super(ListResource, self).__init__(*args, **kwargs)

        try:
            self.key
        except AttributeError:
            self.key = self.name.lower()

    def get(self, sid):
        """ Get an instance resource by its sid

        Usage:

        .. code-block:: python

            message = client.messages.get("SM1234")
            print message.body

        :rtype: :class:`~twilio.rest.resources.InstanceResource`
        :raises: a :exc:`~twilio.TwilioRestException` if a resource with that
            sid does not exist, or the request fails
        """
        return self.get_instance(sid)

    def get_instance(self, sid):
        """Request the specified instance resource"""
        uri = "%s/%s" % (self.uri, sid)
        resp, item = self.request("GET", uri)
        return self.load_instance(item)

    def get_instances(self, params):
        """
        Query the list resource for a list of InstanceResources.

        Raises a :exc:`~twilio.TwilioRestException` if requesting a page of
        results that does not exist.

        :param dict params: List of URL parameters to be included in request
        :param int page: The page of results to retrieve (most recent at 0)
        :param int page_size: The number of results to be returned.

        :returns: -- the list of resources
        """
        params = transform_params(params)

        resp, page = self.request("GET", self.uri, params=params)

        if self.key not in page:
            raise TwilioException("Key %s not present in response" % self.key)

        return [self.load_instance(ir) for ir in page[self.key]]

    def create_instance(self, body):
        """
        Create an InstanceResource via a POST to the List Resource

        :param dict body: Dictionary of POST data
        """
        resp, instance = self.request("POST", self.uri,
                                      data=transform_params(body))

        if resp.status_code not in (200, 201):
            raise TwilioRestException(resp.status_code,
                                      self.uri, "Resource not created")

        return self.load_instance(instance)

    def delete_instance(self, sid):
        """
        Delete an InstanceResource via DELETE

        body: string -- HTTP Body for the quest
        """
        uri = "%s/%s" % (self.uri, sid)
        resp, instance = self.request("DELETE", uri)
        return resp.status_code == 204

    def update_instance(self, sid, body):
        """
        Update an InstanceResource via a POST

        sid: string -- String identifier for the list resource
        body: dictionary -- Dict of items to POST
        """
        uri = "%s/%s" % (self.uri, sid)
        resp, entry = self.request("POST", uri, data=transform_params(body))
        return self.load_instance(entry)

    def iter(self, **kwargs):
        """ Return all instance resources using an iterator

        This will fetch a page of resources from the API and yield them in
        turn. When the page is exhausted, this will make a request to the API
        to retrieve the next page. Hence you may notice a pattern - the library
        will loop through 50 objects very quickly, but there will be a delay
        retrieving the 51st as the library must make another request to the API
        for resources.

        Example usage:

        .. code-block:: python

            for message in client.messages:
                print message.sid
        """
        params = transform_params(kwargs)

        while True:
            resp, page = self.request("GET", self.uri, params=params)

            if self.key not in page:
                raise StopIteration()

            for ir in page[self.key]:
                yield self.load_instance(ir)

            if not page.get('next_page_uri', ''):
                raise StopIteration()

            o = urlparse(page['next_page_uri'])
            params.update(parse_qs(o.query))

    def load_instance(self, data):
        instance = self.instance(self, data[self.instance.id_key])
        instance.load(data)
        instance.load_subresources()
        return instance

    def __str__(self):
        return '<%s>' % (self.__class__.__name__)

    def list(self, **kw):
        """Query the list resource for a list of InstanceResources.

        :param int page: The page of results to retrieve (most recent at 0)
        :param int page_size: The number of results to be returned.
        """
        return self.get_instances(kw)


class NextGenListResource(ListResource):

    name = "Resources"
    instance = NextGenInstanceResource
    use_json_extension = False

    def __init__(self, *args, **kwargs):
        super(NextGenListResource, self).__init__(*args, **kwargs)

    def iter(self, **kwargs):
        """ Return all instance resources using an iterator

        This will fetch a page of resources from the API and yield them in
        turn. When the page is exhausted, this will make a request to the API
        to retrieve the next page. Hence you may notice a pattern - the library
        will loop through 50 objects very quickly, but there will be a delay
        retrieving the 51st as the library must make another request to the API
        for resources.

        Example usage:

        .. code-block:: python

            for message in client.messages:
                print message.sid
        """
        params = urlencode(transform_params(kwargs))
        parsed = urlparse(self.uri)
        url = urlunparse(parsed[:4] + (params, ) + (parsed[5], ))

        while True:
            resp, page = self.request("GET", url)

            key = page.get('meta', {}).get('key')

            if key is None or key not in page:
                raise StopIteration()

            for ir in page[key]:
                yield self.load_instance(ir)

            url = page.get('meta', {}).get('next_page_url')
            if not url:
                raise StopIteration()

    def get_instances(self, params):
        """
        Query the list resource for a list of InstanceResources.

        Raises a :exc:`~twilio.TwilioRestException` if requesting a page of
        results that does not exist.

        :param dict params: List of URL parameters to be included in request
        :param int page: The page of results to retrieve (most recent at 0)
        :param int page_size: The number of results to be returned.

        :returns: -- the list of resources
        """
        params = transform_params(params)

        resp, page = self.request("GET", self.uri, params=params)
        key = page.get('meta', {}).get('key')

        if key is None:
            raise TwilioException(
                "Unable to determine resource key from response"
            )

        if key not in page:
            raise TwilioException("Key %s not present in response" % key)

        return [self.load_instance(ir) for ir in page[key]]
