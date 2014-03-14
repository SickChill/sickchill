"""
The httplib2 algorithms ported for use with requests.
"""
import re
import calendar
import time

from cachecontrol.cache import DictCache
from cachecontrol.compat import parsedate_tz


URI = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")


def parse_uri(uri):
    """Parses a URI using the regex given in Appendix B of RFC 3986.

        (scheme, authority, path, query, fragment) = parse_uri(uri)
    """
    groups = URI.match(uri).groups()
    return (groups[1], groups[3], groups[4], groups[6], groups[8])


class CacheController(object):
    """An interface to see if request should cached or not.
    """
    def __init__(self, cache=None, cache_etags=True):
        self.cache = cache or DictCache()
        self.cache_etags = cache_etags

    def _urlnorm(self, uri):
        """Normalize the URL to create a safe key for the cache"""
        (scheme, authority, path, query, fragment) = parse_uri(uri)
        if not scheme or not authority:
            raise Exception("Only absolute URIs are allowed. uri = %s" % uri)
        authority = authority.lower()
        scheme = scheme.lower()
        if not path:
            path = "/"

        # Could do syntax based normalization of the URI before
        # computing the digest. See Section 6.2.2 of Std 66.
        request_uri = query and "?".join([path, query]) or path
        scheme = scheme.lower()
        defrag_uri = scheme + "://" + authority + request_uri

        return defrag_uri

    def cache_url(self, uri):
        return self._urlnorm(uri)

    def parse_cache_control(self, headers):
        """
        Parse the cache control headers returning a dictionary with values
        for the different directives.
        """
        retval = {}

        cc_header = 'cache-control'
        if 'Cache-Control' in headers:
            cc_header = 'Cache-Control'

        if cc_header in headers:
            parts = headers[cc_header].split(',')
            parts_with_args = [
                tuple([x.strip().lower() for x in part.split("=", 1)])
                for part in parts if -1 != part.find("=")]
            parts_wo_args = [(name.strip().lower(), 1)
                             for name in parts if -1 == name.find("=")]
            retval = dict(parts_with_args + parts_wo_args)
        return retval

    def cached_request(self, url, headers):
        cache_url = self.cache_url(url)
        cc = self.parse_cache_control(headers)

        # non-caching states
        no_cache = True if 'no-cache' in cc else False
        if 'max-age' in cc and cc['max-age'] == 0:
            no_cache = True

        # see if it is in the cache anyways
        in_cache = self.cache.get(cache_url)
        if no_cache or not in_cache:
            return False

        # It is in the cache, so lets see if it is going to be
        # fresh enough
        resp = self.cache.get(cache_url)

        # Check our Vary header to make sure our request headers match
        # up. We don't delete it from the though, we just don't return
        # our cached value.
        #
        # NOTE: Because httplib2 stores raw content, it denotes
        #       headers that were sent in the original response by
        #       adding -varied-$name. We don't have to do that b/c we
        #       are storing the object which has a reference to the
        #       original request. If that changes, then I'd propose
        #       using the varied headers in the cache key to avoid the
        #       situation all together.
        if 'vary' in resp.headers:
            varied_headers = resp.headers['vary'].replace(' ', '').split(',')
            original_headers = resp.request.headers
            for header in varied_headers:
                # If our headers don't match for the headers listed in
                # the vary header, then don't use the cached response
                if headers.get(header, None) != original_headers.get(header):
                    return False

        now = time.time()
        date = calendar.timegm(
            parsedate_tz(resp.headers['date'])
        )
        current_age = max(0, now - date)

        # TODO: There is an assumption that the result will be a
        # requests response object. This may not be best since we
        # could probably avoid instantiating or constructing the
        # response until we know we need it.
        resp_cc = self.parse_cache_control(resp.headers)

        # determine freshness
        freshness_lifetime = 0
        if 'max-age' in resp_cc and resp_cc['max-age'].isdigit():
            freshness_lifetime = int(resp_cc['max-age'])
        elif 'expires' in resp.headers:
            expires = parsedate_tz(resp.headers['expires'])
            if expires is not None:
                expire_time = calendar.timegm(expires) - date
                freshness_lifetime = max(0, expire_time)

        # determine if we are setting freshness limit in the req
        if 'max-age' in cc:
            try:
                freshness_lifetime = int(cc['max-age'])
            except ValueError:
                freshness_lifetime = 0

        if 'min-fresh' in cc:
            try:
                min_fresh = int(cc['min-fresh'])
            except ValueError:
                min_fresh = 0
            # adjust our current age by our min fresh
            current_age += min_fresh

        # see how fresh we actually are
        fresh = (freshness_lifetime > current_age)

        if fresh:
            # make sure we set the from_cache to true
            resp.from_cache = True
            return resp

        # we're not fresh. If we don't have an Etag, clear it out
        if 'etag' not in resp.headers:
            self.cache.delete(cache_url)

        if 'etag' in resp.headers:
            headers['If-None-Match'] = resp.headers['ETag']

        if 'last-modified' in resp.headers:
            headers['If-Modified-Since'] = resp.headers['Last-Modified']

        # return the original handler
        return False

    def add_headers(self, url):
        resp = self.cache.get(url)
        if resp and 'etag' in resp.headers:
            return {'If-None-Match': resp.headers['etag']}
        return {}

    def cache_response(self, request, resp):
        """
        Algorithm for caching requests.

        This assumes a requests Response object.
        """
        # From httplib2: Don't cache 206's since we aren't going to
        # handle byte range requests
        if resp.status_code not in [200, 203]:
            return

        cc_req = self.parse_cache_control(request.headers)
        cc = self.parse_cache_control(resp.headers)

        cache_url = self.cache_url(request.url)

        # Delete it from the cache if we happen to have it stored there
        no_store = cc.get('no-store') or cc_req.get('no-store')
        if no_store and self.cache.get(cache_url):
            self.cache.delete(cache_url)

        # If we've been given an etag, then keep the response
        if self.cache_etags and 'etag' in resp.headers:
            self.cache.set(cache_url, resp)

        # Add to the cache if the response headers demand it. If there
        # is no date header then we can't do anything about expiring
        # the cache.
        elif 'date' in resp.headers:
            # cache when there is a max-age > 0
            if cc and cc.get('max-age'):
                if int(cc['max-age']) > 0:
                    self.cache.set(cache_url, resp)

            # If the request can expire, it means we should cache it
            # in the meantime.
            elif 'expires' in resp.headers:
                if resp.headers['expires']:
                    self.cache.set(cache_url, resp)

    def update_cached_response(self, request, response):
        """On a 304 we will get a new set of headers that we want to
        update our cached value with, assuming we have one.

        This should only ever be called when we've sent an ETag and
        gotten a 304 as the response.
        """
        cache_url = self.cache_url(request.url)

        resp = self.cache.get(cache_url)

        if not resp:
            # we didn't have a cached response
            return response

        # did so lets update our headers
        resp.headers.update(resp.headers)

        # we want a 200 b/c we have content via the cache
        request.status_code = 200

        # update the request as it has the if-none-match header + any
        # other headers that the server might have updated (ie Date,
        # Cache-Control, Expires, etc.)
        resp.request = request

        # update our cache
        self.cache.set(cache_url, resp)

        # Let everyone know this was from the cache.
        resp.from_cache = True

        return resp
