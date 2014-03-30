from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.cache import DictCache
from cachecontrol.session import CacheControlSession

def CacheControl(sess=None, cache=None, cache_etags=True):
    sess = sess or CacheControlSession()
    cache = cache or DictCache()
    adapter = CacheControlAdapter(cache, cache_etags=cache_etags)
    sess.mount('http://', adapter)

    return sess
