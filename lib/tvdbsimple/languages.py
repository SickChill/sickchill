# -*- coding: utf-8 -*-

"""
This module implements the Language functionality of TheTVDb API.
Allows to retrieve the languages list and info.

See [Languages API section](https://api.thetvdb.com/swagger#!/Languages)
"""
import sys
if sys.version_info > (2, 8):
    from builtins import dict
from .base import TVDB

class Languages(TVDB):
    """
    Languages class to retrieve the languages list and info.
    """
    _BASE_PATH = 'languages'
    _URLS = {
        'all': '',
        'language': '/{lid}'
    }
    LANGUAGES = {}
    _ALL_PARSED = False

    def all(self):
        """
        Get the full languages list and set it to all attribute.

        Returns a list of languages with their info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> lng = tvdb.Languages()
            >>> response = lng.all()
            >>> lng.all[0]['englishName']
            'Chinese'

        """
        if self._ALL_PARSED:
            return self.LANGUAGES.values()
            
        path = self._get_path('all')
        
        response = self._GET(path)
        self._set_attrs_to_values({'all': response})
        for lang in response:
            if 'id' in lang:
                self.LANGUAGES[lang['id']] = lang
        self._ALL_PARSED = True
        return response

    def language(self, id):
        """
        Get the language info for a specific language id.
        
        `id` is the specific language id to retrieve.

        Returns a dict rwith all the language info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> lng = tvdb.Languages()
            >>> response = lng.language(7)
            >>> response['englishName']
            'English'

        """
        if id in self.LANGUAGES:
            return self.LANGUAGES[id]

        path = self._get_path('language').format(lid=id)
        
        response = self._GET(path)
        if 'id' in response:
            self.LANGUAGES[response['id']] = response
        return response

    def __iter__(self):
        for i in self.all():
            yield i

    def __getitem__(self, id):
        return self.language(id)

    def __setitem__(self):
        raise Exception('Function Disabled')
        
    def __delitem__(self):
        raise Exception('Function Disabled')
