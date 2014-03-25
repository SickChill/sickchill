#!/usr/bin/env python2
#encoding:utf-8
#author:echel0n
#project:indexer_api
#repository:http://github.com/echel0n/Sick-Beard
#license:unlicense (http://unlicense.org/)

"""Custom exceptions used or raised by indexer_api"""

__author__ = "echel0n"
__version__ = "1.0"

from lib.tvrage_api.tvrage_exceptions import \
    tvrage_exception, tvrage_attributenotfound, tvrage_episodenotfound, tvrage_error, \
    tvrage_seasonnotfound, tvrage_shownotfound, tvrage_userabort

from lib.tvdb_api.tvdb_exceptions import \
    tvdb_exception, tvdb_attributenotfound, tvdb_episodenotfound, tvdb_error, \
    tvdb_seasonnotfound, tvdb_shownotfound, tvdb_userabort

indexerExcepts = ["indexer_exception", "indexer_error", "indexer_userabort", "indexer_shownotfound",
                  "indexer_seasonnotfound", "indexer_episodenotfound", "indexer_attributenotfound"]

tvdbExcepts = ["tvdb_exception", "tvdb_error", "tvdb_userabort", "tvdb_shownotfound",
               "tvdb_seasonnotfound", "tvdb_episodenotfound", "tvdb_attributenotfound"]

tvrageExcepts = ["tvdb_exception", "tvrage_error", "tvrage_userabort", "tvrage_shownotfound",
                 "tvrage_seasonnotfound", "tvrage_episodenotfound", "tvrage_attributenotfound"]

# link API exceptions to our exception handler
indexer_exception = tvdb_exception, tvrage_exception
indexer_error = tvdb_error, tvrage_error
indexer_userabort = tvdb_userabort, tvrage_userabort
indexer_attributenotfound = tvdb_attributenotfound, tvrage_attributenotfound
indexer_episodenotfound = tvdb_episodenotfound, tvrage_episodenotfound
indexer_seasonnotfound = tvdb_seasonnotfound, tvrage_seasonnotfound
indexer_shownotfound = tvdb_shownotfound, tvrage_shownotfound