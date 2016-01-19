__version__ = "0.1"

'''
Usage: 
from lib.anidbhttp import anidbquery
from lib.anidbhttp.query import QUERY_HOT
result = anidbquery.query(QUERY_HOT)
'''
from .query import AnidbQuery

anidbquery = AnidbQuery('sickragehttp',1)