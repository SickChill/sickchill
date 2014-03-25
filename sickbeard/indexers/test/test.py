from __future__ import with_statement

import unittest

import sys
import datetime
import os.path
import string

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../../../lib'))

import sickbeard
import itertools

from itertools import chain
from sickbeard import classes


class APICheck(unittest.TestCase):
    indexer = u'3'

    for i in int([indexer]) and sickbeard.indexerApi().indexers:
        print i

    global indexer, keywords, nameUTF8

    indexer = 0
    name = 'american dad'
    lang = "en"

    if not lang or lang == 'null':
        lang = "en"

    results = []

    nameUTF8 = name.encode('utf-8')

    # Use each word in the show's name as a possible search term
    keywords = nameUTF8.split(' ')

    # Insert the whole show's name as the first search term so best results are first
    # ex: keywords = ['Some Show Name', 'Some', 'Show', 'Name']
    if len(keywords) > 1:
        keywords.insert(0, nameUTF8)


    # check for indexer preset
    indexers = [int(indexer)]
    if 0 in indexers:
        indexers = sickbeard.indexerApi().indexers

    # Query Indexers for each search term and build the list of results
    for i in indexers:
        def searchShows(i):
            results = []

            lINDEXER_API_PARMS = {'indexer': i}
            lINDEXER_API_PARMS['custom_ui'] = classes.AllShowsListUI
            t = sickbeard.indexerApi(**lINDEXER_API_PARMS)

            for searchTerm in keywords:
                try:
                    search = t[searchTerm]
                    if isinstance(search, dict):
                        search = [search]

                    # add search results
                    result = [
                        [t.name, t.config['id'], t.config["show_url"], int(x['id']), x['seriesname'], x['firstaired']]
                        for x in search if nameUTF8.lower() in x['seriesname'].lower()]

                    # see if we have any matches
                    if len(result) > 0:
                        # add result to list of found shows
                        results += result

                        # search through result to see if we have a exact match
                        for show in result:
                            # cleanup the series name
                            seriesname = show[4].encode('utf-8').translate(None, string.punctuation)

                            # check if we got a exact match
                            if nameUTF8.lower() == seriesname.lower():
                                return results

                except Exception, e:
                    continue

            # finished searching a indexer so return the results
            return results

        # search indexers for shows
        results += searchShows(i)

    # remove duplicates
    results = list(results for results, _ in itertools.groupby(results))
    print results

    if __name__ == "__main__":
        unittest.main()