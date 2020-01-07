# -*- coding: utf-8 -*-

"""
This module implements the Series functionality of TheTVDb API.
Allows to retrieve series info, actors, basic episodes info and images.

See [Series API section](https://api.thetvdb.com/swagger#/Series)
"""

from .base import TVDB

class Series(TVDB):
    """
    Series class to retrieve all the info about a series.
    Requires the series id.
    """
    _BASE_PATH = 'series'
    _URLS = {
        'info': '/{id}',
        'actors': '/{id}/actors'
    }	

    def __init__(self, id, language=''):
        """
        Initialize the series class.
        `id` is the TheTVDb series id. You can also provide `language`, 
        the language id you want to use to retrieve the info.
        """
        self._set_language(language)
        self.Images = Series_Images(id, language)
        """
        Allows to retrieve images info.
        """
        self.Episodes = Series_Episodes(id, language)
        """
        Allows to retrieve episodes info.
        """
        super(Series, self).__init__(id)

    def info(self, language=''):
        """
        Get the basic show information for a specific show id and sets 
        them to the attributes.

        You also provide `language`, the language id you want to use 
        to retrieve the info.

        Returns a dict with the series info

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> show = tvdb.Series(78804)
            >>> response = show.info()
            >>> show.seriesName
            'Doctor Who (2005)'

        """
        path = self._get_id_path('info')
        
        self._set_language(language)
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response

    def actors(self, language=''):
        """
        Get the actors for the show id and sets them to 
        `actors` the attributes.

        You also provide `language`, the language id you want to use 
        to retrieve the info.

        Returns a list of actors with their info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> show = tvdb.Series(78804)
            >>> response = show.actors()
            >>> show.actors[0]['name']
            u'David Tennant'

        """
        path = self._get_id_path('actors')
        
        self._set_language(language)
        response = self._GET(path)
        self._set_attrs_to_values({'actors': response})
        return response

class Series_Episodes(TVDB):
    """
    Class needed to organize series episodes. Allow to retrieve basic 
    info episodes for the series.
    Requires the series id.
    """
    _BASE_PATH = 'series'
    _URLS = {
        'summary': '/{id}/episodes/summary',
        'episodes': '/{id}/episodes',
        'query': '/{id}/episodes/query',
        'query_params': '/{id}/episodes/query/params'
    }

    def __init__(self, id, language='', **kwargs):
        """
        Initialize the class.

        `id` is the TheTVDb series id.
        You can  provide `language`, the language id you want to use to 
        retrieve the info.
        You can  provide `absoluteNumber` to get only episodes with the 
        provided absolute number.
        You can  provide `airedSeason` to get only episodes with the 
        provided aired season number.
        You can  provide `airedEpisode` to get only episodes with the 
        provided aired episode number.
        You can  provide `dvdSeason` to get only episodes with the 
        provided dvd season number.
        You can  provide `dvdEpisode` to get only episodes with the 
        provided dvd episode number.
        You can  provide `imdbId` to get only episodes with the 
        provided imdb id.
        """
        super(Series_Episodes, self).__init__(id)
        self._set_language(language)
        self._FILTERS = {}
        self.update_filters(**kwargs)
        self._PAGES = -1
        self._PAGES_LIST = {}

    def update_filters(self, **kwargs):
        """
        Set the filters for the episodes of the specific show id.

        You can  provide `absoluteNumber` to get only episodes with the 
        provided absolute number.
        You can  provide `airedSeason` to get only episodes with the 
        provided aired season number.
        You can  provide `airedEpisode` to get only episodes with the 
        provided aired episode number.
        You can  provide `dvdSeason` to get only episodes with the 
        provided dvd season number.
        You can  provide `dvdEpisode` to get only episodes with the 
        provided dvd episode number.
        You can  provide `imdbId` to get only episodes with the 
        provided imdb id.
        """
        self._PAGES = -1
        self._PAGES_LIST = {}
        self._FILTERS=kwargs

    def summary(self):
        """
        Get the episodes summary for a specific show id and sets 
        them to their attributes.

        Returns a dict with a summary of the episodes.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showeps = tvdb.Series_Episodes(78804)
            >>> response = showeps.summary()
            >>> showeps.airedEpisodes
            '267'

        """
        path = self._get_id_path('summary')
        
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response

    def query_params(self):
        """
        Get the query parameters allowed for a specific show id.

        Returns a dict with all the filters allowed.
        """
        path = self._get_id_path('query_params')
        
        response = self._GET(path)
        self._set_attrs_to_values({'query_params': response})
        return response

    def pages(self):
        """
        Get the number of episode pages for filtered episodes of a specific show id.

        Returns the integer number of pages for filtered episodes of the show.
        """
        if self._PAGES < 0:
            self.page(1)
        return self._PAGES

    def all(self):
        """
        Get the full episode list with basic details for a specific show id.
        
        Returns a list of episodes with basic info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showeps = tvdb.Series_Episodes(78804)
            >>> response = showeps.all()
            >>> showeps.episodes[0]['episodeName']
            'Rose'

        """
        episodes = []
        for i in range (1, self.pages()+1):
            episodes.extend(self.page(i))
        
        self._set_attrs_to_values({'episodes': episodes})
        return episodes

    def page(self, page):
        """
        Get the episode list for a specific page of a show id.
        `page` is the page number of the episodes list to retrieve

        Returns a list episodes with basic info.
        """
        if page in self._PAGES_LIST:
            return self._PAGES_LIST[page]
        if self._FILTERS:
            path = self._get_id_path('query')
        else:
            path = self._get_id_path('episodes')
        
        filters = self._FILTERS.copy()
        filters['page'] = page
        response = self._GET(path, params=filters, cleanJson=False)
        if 'links' in response and 'last' in response['links']:
            self._PAGES = response['links']['last']

        self._PAGES_LIST[page] = response['data']
        return response['data']

    def __iter__(self):
        for i in range (1, self.pages()+1):
            yield self.page(i)

class Series_Images(TVDB):
    """
    Class needed to organize series images. Allow to retrieve all 
    the types of images of a series.
    Requires the series id.

        language: (optional) language to request.
        resolution: (optional) image resolution.
        subKey: (optional) subkey research.
    """
    _BASE_PATH = 'series'
    _URLS = {
        'imagequery': '/{id}/images/query',
        'summary': '/{id}/images',
        'query_params': '/{id}/images/query/params'
    }

    def __init__(self, id, language='', **kwargs):
        """
        Initialize the class.

        `id` is the TheTVDb series id.
        You can  provide `language`, the language id you want to use to 
        retrieve the info.
        You can  provide `reqolution` to get only episodes with the 
        provided resolution.
        You can  provide `subKey` to get only episodes with the 
        provided subKey.
        """
        super(Series_Images, self).__init__(id)
        self._set_language(language)
        self.update_filters(**kwargs)

    def update_filters(self, **kwargs):
        """
        Set the filters for the episodes of the specific show id.

        You can  provide `language`, the language id you want to use to 
        retrieve the info.
        You can  provide `reqolution` to get only episodes with the 
        provided resolution.
        You can  provide `subKey` to get only episodes with the 
        provided subKey.
        """
        self._FILTERS=kwargs

    def summary(self):
        """
        Get the images summary for a specific show id and sets 
        them to `summary` attributes.

        Returns a dict with a summary of the images.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.summary()
            >>> showimgs.summary['poster']
            53

        """
        path = self._get_id_path('summary')
        
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response

    def query_params(self):
        """
        Get the query parameters allowed for a specific show id.

        Returns:
            A dict respresentation of the JSON returned from the API.
        """
        path = self._get_id_path('query_params')
        
        response = self._GET(path)
        self._set_attrs_to_values({'query_params': response})
        return response


    def poster(self, language=''):
        """
        Get the posters for a specific show.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of posters.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.poster()
            >>> showimgs.poster[0]['resolution']
            '680x1000'

        """
        return self._get_image_type('poster', language)

    def fanart(self, language=''):
        """
        Get the fanarts for a specific show.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of fanarts.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.fanart()
            >>> showimgs.fanart[0]['resolution']
            '1280x720'

        """
        return self._get_image_type('fanart', language)

    def series(self, language=''):
        """
        Get the series images for a specific show.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of series images.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.series()
            >>> showimgs.series[0]['thumbnail']
            '_cache/text/34391.jpg'

        """
        return self._get_image_type('series', language)

    def season(self, language=''):
        """
        Get the season images for a specific show.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of season images.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.season()
            >>> showimgs.season[0]['thumbnail']
            '_cache/seasons/34391-1.jpg'

        """
        return self._get_image_type('season', language)

    def seasonwide(self, language=''):
        """
        Get the seasonwide images for a specific show.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of seasonwide images.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804)
            >>> response = showimgs.seasonwide()
            >>> showimgs.seasonwide[0]['thumbnail']
            '_cache/seasonswide/78804-1.jpg'

        """
        return self._get_image_type('seasonwide', language)

    def all(self, language=''):
        """
        Get all the images for a specific show and sets it to `images` attribute.
        It needs to have at least one filter set.
        
        You can  provide `language`, the language id you want to use to 
        retrieve the info.

        Returns a list of images.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> showimgs = tvdb.Series_Images(78804, resolution='1280x720')
            >>> response = showimgs.all()
            >>> showimgs.images[0]['resolution']
            '1280x720'

        """
        return self._get_image_type('images', language)

    def _get_image_type(self, type, language=''):
        path = self._get_id_path('imagequery')
        
        self._set_language(language)
        filters = self._FILTERS.copy()
        if type != 'images':
            filters['keyType'] = type

        response = self._GET(path, params=filters)
        self._set_attrs_to_values({type: response})
        return response
