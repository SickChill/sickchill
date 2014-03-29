from requests.adapters import HTTPAdapter

from cachecontrol.controller import CacheController
from cachecontrol.cache import DictCache


class CacheControlAdapter(HTTPAdapter):
    invalidating_methods = set(['PUT', 'DELETE'])

    def __init__(self, sess=None, cache=None, cache_etags=True, *args, **kw):
        super(CacheControlAdapter, self).__init__(*args, **kw)
        self.cache = cache or DictCache()
        self.controller = CacheController(sess=sess, cache=cache, cache_etags=cache_etags)

    def send(self, request, **kw):
        """Send a request. Use the request information to see if it
        exists in the cache.
        """
        if request.method == 'GET':
            cached_response = self.controller.cached_request(
                request.url, request.headers
            )
            if cached_response:
                # Cached responses should not have a raw field since
                # they *cannot* be created from some stream.
                cached_response.raw = None
                return cached_response

            # check for etags and add headers if appropriate
            headers = self.controller.add_headers(request.url)
            request.headers.update(headers)

        resp = super(CacheControlAdapter, self).send(request, **kw)
        return resp

    def build_response(self, request, response):
        """Build a response by making a request or using the cache.

        This will end up calling send and returning a potentially
        cached response
        """
        resp = super(CacheControlAdapter, self).build_response(
            request, response
        )

        # See if we should invalidate the cache.
        if request.method in self.invalidating_methods and resp.ok:
            cache_url = self.controller.cache_url(request.url)
            self.cache.delete(cache_url)

        # Try to store the response if it is a GET
        elif request.method == 'GET':
            if response.status == 304:
                # We must have sent an ETag request. This could mean
                # that we've been expired already or that we simply
                # have an etag. In either case, we want to try and
                # update the cache if that is the case.
                resp = self.controller.update_cached_response(
                    request, response
                )
                # Fix possible exception when using missing `raw` field in
                # requests
                # TODO: remove when requests will be bump to 2.2.2 or 2.3
                # version
                resp.raw = None
            else:
                # try to cache the response
                self.controller.cache_response(request, resp)

        # Give the request a from_cache attr to let people use it
        # rather than testing for hasattr.
        if not hasattr(resp, 'from_cache'):
            resp.from_cache = False

        return resp
