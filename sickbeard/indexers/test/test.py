from __future__ import with_statement

import unittest

import sqlite3

import sys
import os.path
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import sickbeard
import shutil

from sickbeard import encodingKludge as ek, providers, tvcache
from sickbeard import db
from sickbeard.databases import mainDB
from sickbeard.databases import cache_db


from indexer_api import indexerApi
from indexer_exceptions import indexer_exception

class APICheck(unittest.TestCase):
    indexer_id = 258171
    indexer = 'Tvdb'
    # Set our common indexer_api options here
    INDEXER_API_PARMS = {'apikey': '9DAF49C96CBF8DAC',
                      'language': 'en',
                      'useZip': True}


    INDEXER_API_PARMS['indexer'] = indexer
    lindexer_api_parms = INDEXER_API_PARMS.copy()

    try:
        imdbid = " "
        showurl = indexerApi(**lindexer_api_parms).config['base_url'] + indexer_id + '/all/en.zip'
        t = indexerApi().config['valid_languages']
        t = indexerApi(**lindexer_api_parms)
        myEp = t[258171]

        if getattr(myEp, 'seriesname', None) is not None:
            print "FOUND"

    except indexer_exception as e:
        print e
        pass

if __name__ == "__main__":
    unittest.main()