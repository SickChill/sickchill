# -*- coding: utf-8 -*-

"""
This module implements the Updates functionality of TheTVDb API.
Allows to retrieve updated series in a timespan.

See [Updates API section](https://api.thetvdb.com/swagger#!/Updates)
"""

from .base import TVDB

class Updates(TVDB):
    """
    Updates class to retrieve updated series in a timespan.
    Requires `fromTime` that is the starting date of the updates.
    """
    _BASE_PATH = 'updated'
    _URLS = {
        'query': '/query',
        'update_params': '/query/params'
    }

    def __init__(self, fromTime, toTime='', language=''):
        """
        Initialize the Updates class.
        `fromTime` is the epoch time to start your date range to search for.
        You can set `toTime` to set the epoch time to end your date range. 
        Must be one week from `fromTime`.
        You can also set `language` with a language id to get the result 
        in the specific language.
        """
        self._FILTERS = {}
        self.update_filters(fromTime, toTime, language)

    def update_filters(self, fromTime='', toTime='', language=''):
        """
        Updates the filters for the updates class.

        `fromTime` is the epoch time to start your date range to search for.
        You can set `toTime` to set the epoch time to end your date range. 
        Must be one week from `fromTime`.
        You can also set `language` with a language id to get the result 
        in the specific language.
        """
        if fromTime:
            self._FILTERS['fromTime'] = fromTime
        if fromTime:
            self._FILTERS['toTime'] = toTime
        if language:
            self._set_language(language)

    def series(self):
        """
        Get the series updated in the set time span (maximom one week from fromTime).

        Returns a list of series updated in the timespan with basic info
        """
        path = self._get_path('query')
        
        response = self._GET(path, params=self._FILTERS)
        self._set_attrs_to_values({'series': response})
        return response

    def update_params(self):
        """
        Get the filters available for the updated api.

        Returns a list of filters available for updates.
        """
        path = self._get_path('update_params')
        
        response = self._GET(path)
        self._set_attrs_to_values({'update_params': response})
        return response
