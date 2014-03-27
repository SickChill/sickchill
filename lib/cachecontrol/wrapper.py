from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.cache import DictCache


def CacheControl(sess, cache=None, cache_etags=True, cache_all=False):
    cache = cache or DictCache()
    adapter = CacheControlAdapter(cache, cache_etags=cache_etags, cache_all=cache_all)
    sess.mount('http://', adapter)

    return sess
