# -*- coding: utf-8 -*-

"""
This module implements the User functionality of TheTVDb API.
Allows to retrieve, add and delete user favorites and ratings.

See [Users API section](https://api.thetvdb.com/swagger#!/Users)
"""

from .base import TVDB

class User(TVDB):
    """
    User class to retrieve, add and delete user favorites and ratings.
    Requires username and user-key.
    """
    _BASE_PATH = 'user'
    _URLS = {
        'info': '',
        'favorites': '/favorites',
        'alter_favorite': '/favorites/{id}'
    }

    def __init__(self, user, key):
        """
        Initialize the User class.

        `user` is the username for login. `key` is the userkey needed to 
        authenticate with the user, you can find it in the 
        [account info](http://thetvdb.com/?tab=userinfo) under account identifier.
        """
        super(User, self).__init__(user=user, key=key)
        self.Ratings = User_Ratings(user, key)
        """
        Allows to retrieve, add and delete user ratings.
        """

    def info(self):
        """
        Get the basic user info and set its values to local attributes.
        
        Returns a dict with all the information of the user.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> user = tvdb.User('username', 'userkey')
            >>> response = user.info()
            >>> user.userName
            'username'

        """
        path = self._get_path('info')
        
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return response

    def favorites(self):
        """
        Get the a list of the favorite series of the user and
        sets it to `favorites` attribute.
        
        Returns a list of the favorite series ids.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> user = tvdb.User('username', 'userkey')
            >>> response = user.favorites()
            >>> user.favorites[0]
            '73545'

        """
        path = self._get_path('favorites')
        
        response = self._GET(path)
        self._set_attrs_to_values(response)
        return self._clean_return(response)

    def _clean_return(self,jsn):
        if 'favorites' in jsn:
            return jsn['favorites']
        return jsn

    def add_favorite(self, id):
        """
        Add a series to user favorite series from its series id.
        
        `id` is the series id you want to add to favorites.

        Returns the updated list of the favorite series ids.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> user = tvdb.User('username', 'userkey')
            >>> response = user.add_favorite(78804)
            >>> response[-1]
            '78804'

        """
        path = self._get_path('alter_favorite').format(id=id)
        
        return self._clean_return(self._PUT(path))

    def delete_favorite(self, id):
        """
        Delete a series from user favorite series from its series id.
        
        `id` is the series id you want to delete from favorites.

        Returns the updated list of the favorite series ids.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> user = tvdb.User('username', 'userkey')
            >>> response = user.delete_favorite(78804)
            >>> response[-1]
            '73545'

        """
        path = self._get_path('alter_favorite').format(id=id)
        
        return self._clean_return(self._DELETE(path))

class User_Ratings(TVDB):
    """
    Class needed to organize user ratings. Allows to retrieve, add and delete user ratings.

    Requires username and user-key.
    """
    _BASE_PATH = 'user/ratings'
    _URLS = {
        'all': '',
        'query': '/query',
        'query_params': '/query/params',
        'add': '/{itemType}/{itemId}/{itemRating}',
        'delete': '/{itemType}/{itemId}'
    }

    def __init__(self, user, key, **kwargs):
        """
        Initialize the class.

        `user` is the username for login. `key` is the userkey needed to 
        authenticate with the user, you can find it in the 
        [account info](http://thetvdb.com/?tab=userinfo) under account identifier.
        It's possible to provide `itemType` that filters ratings by type. 
        Can be either 'series', 'episode', or 'banner'.
        """
        super(User_Ratings, self).__init__(user=user, key=key)
        self.update_filters(**kwargs)

    def update_filters(self, **kwargs):
        """
        Set the filters for the user rating.

        It's possible to provide `itemType` that filters ratings by type. 
        Can be either 'series', 'episode', or 'banner'.
        """
        self._PAGES = -1
        self._PAGES_LIST = {}
        self._FILTERS = kwargs

    def query_params(self):
        """
        Get the query parameters allowed for filtering and set it to `query_params` attribute.

        Returns a list of parameters you can set to filters.
        """
        path = self._get_id_path('query_params')
        
        response = self._GET(path)
        self._set_attrs_to_values({'query_params': response})
        return response

    def pages(self):
        """
        Get the number of rating pages available for filtered ratings of the specific user.

        Returns the number of rating pages available with current filters.
        """
        if self._PAGES < 0:
            self.page(1)
        return self._PAGES

    def add(self, type, id, rating):
        """
        Add a new rating to the user's ratings..
        
        `type` is the item type of the item you want to rate. Can be either 
        'series', 'episode', or 'image'.
        `id` is the ID of the item that you want to rate.
        `rating` is the `integer` rating you want to set.

        Returns a list with the new updated rating.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> rtn = tvdb.User_Ratings('username', 'userkey')
            >>> response = rtn.add('series', 78804, 8)

        """
        path = self._get_path('add').format(itemType=type, itemId=id, itemRating=rating)
        
        return self._PUT(path)

    def delete(self, type, id):
        """
        Delete an existing user's rating..
        
        `type` is the item type of the item rating you want to delete. Can be either 
        'series', 'episode', or 'image'.
        `id` is the ID of the item rating that you want to delete.

        Returns an empty dictionary.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> rtn = tvdb.User_Ratings('username', 'userkey')
            >>> response = rtn.delete('series', 78804)

        """
        path = self._get_path('delete').format(itemType=type, itemId=id)
        
        return self._DELETE(path)

    def all(self):
        """
        Get the full rating list filtered for the user and adds it
        to the `ratings` attribute.
        
        Returns a list of ratings info.

        For example

            #!python
            >>> import tvdbsimple as tvdb
            >>> tvdb.KEYS.API_KEY = 'YOUR_API_KEY'
            >>> rtn = tvdb.User_Rating('phate89', '3EF7CF9BBC8BB430')
            >>> response = rtn.all()
            >>> rtn.ratings[0]['ratingType']
            'episode'

        """
        ratings = []
        for i in range (1, self.pages()+1):
            ratings.extend(self.page(i))
        
        self._set_attrs_to_values({'ratings': ratings})
        return ratings

    def page(self, page):
        """
        Get the rating list for a specific page for the user.
        
        `page` is the rating page number.

        Returns a list ratings available in the page.
        """
        if page in self._PAGES_LIST:
            return self._PAGES_LIST[page]
        if self._FILTERS:
            path = self._get_path('query')
        else:
            path = self._get_path('all')
        
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