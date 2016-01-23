try:
    import cPickle as pickle
except ImportError:
    import pickle
import datetime

from os.path import join, isfile, isdir
from os import mkdir

__all__ = ["get", "save"]

CACHEDIR = "/tmp/pyanihttp.cache"

def get(aid):
    if not isdir(CACHEDIR):
        mkdir(CACHEDIR)
    cfile = join(CACHEDIR, str(aid))
    if isfile(cfile):
        with open(cfile, "rb") as pfile:
            data = pickle.load(pfile)
            oldtime = data["time"]
            now = datetime.datetime.utcnow()
            diff = now - oldtime
            if diff.days > 1:
                # We can request the information again
                return None
            return data["anime"]
    else:
        return None

def save(aid, anime):
    if not isdir(CACHEDIR):
        mkdir(CACHEDIR)
    data = {"aid": aid,
            "time": datetime.datetime.utcnow(),
            "anime": anime
            }
    cfile = join(CACHEDIR, str(aid))
    with open(cfile, "wb") as pfile:
        pickle.dump(data, pfile)
