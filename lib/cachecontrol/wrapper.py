from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.cache import DictCache


def CacheControl(sess, cache=None, cache_etags=True, cache_force=False):
    cache = cache or DictCache()
    adapter = CacheControlAdapter(cache, cache_etags=cache_etags, cache_force=cache_force)
    sess.mount('http://', adapter)

    return sess
