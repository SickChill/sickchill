import sys
import logging
import traceback

from indexer_api import indexerApi
from indexer_exceptions import indexer_exception

# Set our common indexer_api options here
INDEXER_API_PARMS = {'apikey': '9DAF49C96CBF8DAC',
                  'language': 'en',
                  'useZip': True}


INDEXER_API_PARMS['indexer'] = 'Tvdb'
lindexer_api_parms = INDEXER_API_PARMS.copy()

try:
    imdbid = " "

    t = indexerApi().config['valid_languages']
    t = indexerApi(**lindexer_api_parms)
    myEp = t[258171]

    if getattr(myEp, 'seriesname', None) is not None:
        print "FOUND"

except indexer_exception as e:
    print e
    pass
