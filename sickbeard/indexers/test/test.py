from __future__ import with_statement

import unittest

import sys
import datetime
import os.path
import string

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../../../lib'))

import sickbeard

class APICheck(unittest.TestCase):
    indexer_id = 2930
    lang = "en"

    for indexer in sickbeard.indexerApi.indexers():
        print indexer
        print sickbeard.indexerApi().config['langabbv_to_id'][lang]
        print sickbeard.indexerApi(indexer).cache
        print sickbeard.indexerApi(indexer).name
        print sickbeard.indexerApi(indexer).config['scene_url']
        print sickbeard.indexerApi().config['valid_languages']

        lINDEXER_API_PARMS = sickbeard.indexerApi(indexer).api_params.copy()
        lINDEXER_API_PARMS['cache'] = True
        t = sickbeard.indexerApi(indexer).indexer(**lINDEXER_API_PARMS)
        epObj = t[indexer_id].airedOn(1)[0]

        season = int(epObj["seasonnumber"])
        episodes = [int(epObj["episodenumber"])]

    if __name__ == "__main__":
        unittest.main()