# -*- coding: utf-8 -*-

"""
tmdbsimple.configuration
~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the Configuration, Certifications, and Timezones 
functionality of tmdbsimple.

Created by Celia Oakley on 2013-10-31.

:copyright: (c) 2013-2020 by Celia Oakley
:license: GPLv3, see LICENSE for more details
"""

from .base import TMDB


class Configuration(TMDB):
    """
    Configuration functionality.

    See: https://developers.themoviedb.org/3/configuration
    """
    BASE_PATH = 'configuration'
    URLS = {
        'info': '',
        'languages': '/languages',
    }

    def info(self, **kwargs):
        """
        Get the system wide configuration info.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('info')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

    def languages(self, **kwargs):
        """
        Get the list of languages (ISO 639-1 tags) used throughout TMDb.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('languages')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Certifications(TMDB):
    """
    Certifications functionality.

    See: https://developers.themoviedb.org/3/certifications
    """
    BASE_PATH = 'certification'
    URLS = {
        'movie_list': '/movie/list',
    }

    def list(self, **kwargs):
        """
        Get the list of supported certifications for movies.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('movie_list')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response


class Timezones(TMDB):
    """
    Timezones functionality.

    See: https://developers.themoviedb.org/3/timezones
    """
    BASE_PATH = 'timezones'
    URLS = {
        'list': '/list',
    }

    def list(self, **kwargs):
        """
        Get the list of supported timezones for the API methods that support
        them.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_path('list')

        response = self._GET(path, kwargs)
        self._set_attrs_to_values(response)
        return response

