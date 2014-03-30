from requests.sessions import Session

class CacheControlSession(Session):
    def __init__(self):
        super(CacheControlSession, self).__init__()

    def get(self, *args, **kw):
        # auto-cache response
        self.cache_auto = False
        if kw.get('cache_auto'):
            self.cache_auto = kw.pop('cache_auto')

        # urls allowed to cache
        self.cache_urls = []
        if kw.get('cache_urls'):
            self.cache_urls = [str(args[0])] + kw.pop('cache_urls')

        # timeout for cached responses
        self.cache_max_age = None
        if kw.get('cache_max_age'):
            self.cache_max_age = int(kw.pop('cache_max_age'))

        return super(CacheControlSession, self).get(*args, **kw)

    def prepare_request(self, *args, **kw):
        # get response
        req = super(CacheControlSession, self).prepare_request(*args, **kw)

        # attach params to request
        req.cache_auto = self.cache_auto
        req.cache_urls = self.cache_urls
        req.cache_max_age = self.cache_max_age

        return req