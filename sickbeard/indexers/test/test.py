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

    lINDEXER_API_PARMS = sickbeard.indexerApi(2).api_params.copy()
    t = sickbeard.indexerApi(2).indexer(**lINDEXER_API_PARMS)
    epObj = t[2930]
    print epObj

    if __name__ == "__main__":
        unittest.main()