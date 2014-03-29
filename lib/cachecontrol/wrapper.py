from cachecontrol.session import CacheControlSession
from cachecontrol.adapter import CacheControlAdapter
from cachecontrol.cache import DictCache

def CacheControl(sess=None, cache=None, cache_etags=True):
    sess = sess or CacheControlSession()
    cache = cache or DictCache()
    adapter = CacheControlAdapter(sess, cache, cache_etags=cache_etags)
    sess.mount('http://', adapter)

    return sess
