"""
adapter.py
~~~~~~~~~~

Contains an implementation of an HTTP adapter for Requests that is aware of the
cache contained in this module.
"""
from requests.adapters import HTTPAdapter
from .cache import HTTPCache


class CachingHTTPAdapter(HTTPAdapter):
    """
    A HTTP-caching-aware Transport Adapter for Python Requests. The central
    portion of the API.

    :param capacity: The maximum capacity of the backing cache.
    """
    def __init__(self, capacity=50, **kwargs):
        super(CachingHTTPAdapter, self).__init__(**kwargs)

        #: The HTTP Cache backing the adapter.
        self.cache = HTTPCache(capacity=capacity)

    def send(self, request, **kwargs):
        """
        Sends a PreparedRequest object, respecting RFC 2616's rules about HTTP
        caching. Returns a Response object that may have been cached.

        :param request: The Requests :class:`PreparedRequest <PreparedRequest>` object to send.
        """
        cached_resp = self.cache.retrieve(request)

        if cached_resp is not None:
            return cached_resp
        else:
            return super(CachingHTTPAdapter, self).send(request, **kwargs)

    def build_response(self, request, response):
        """
        Builds a Response object from a urllib3 response. May involve returning
        a cached Response.

        :param request: The Requests :class:`PreparedRequest <PreparedRequest>` object sent.
        :param response: The urllib3 response.
        """
        resp = super(CachingHTTPAdapter, self).build_response(request,
                                                              response)

        if resp.status_code == 304:
            resp = self.cache.handle_304(resp)
        else:
            self.cache.store(resp)

        return resp
