from .adapter import CacheControlAdapter
from .cache import DictCache
from .session import CacheControlSession

def CacheControl(sess=None, cache=None, cache_etags=True, serializer=None):
    sess = sess or CacheControlSession()
    cache = cache or DictCache()
    adapter = CacheControlAdapter(
        cache,
        cache_etags=cache_etags,
        serializer=serializer,
    )
    sess.mount('http://', adapter)
    sess.mount('https://', adapter)

    return sess
