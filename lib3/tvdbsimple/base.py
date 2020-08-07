# -*- coding: utf-8 -*-

"""
This module implements the base class of tvdbsimple.

Handle automatically login, token creation and response basic stripping.

[See Authentication API section](https://api.thetvdb.com/swagger#!/Authentication)
"""

import json
import requests


class AuthenticationError(Exception):
    """
    Authentication exception class for authentication errors
    """
    pass

class APIKeyError(Exception):
    """
    Missing API key exception class in case of missing api
    """
    pass

class TVDB(object):
    """
    Basic Authentication class for API key, login and token automatic handling functionality.

    [See Authentication API section](https://api.thetvdb.com/swagger#!/Authentication)
    """
    _headers = {'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Connection': 'close'}
    _BASE_PATH = ''
    _URLS = {}
    _BASE_URI = 'https://api.thetvdb.com'

    def __init__(self, id=0, user=None, key=None):
        """
        Initialize the base class.
        
        You can provide `id` that is the item id used for url creation. You can also 
        provide `user`, that is the username for login. 
        You can also provide `key`, that is the userkey needed to 
        authenticate with the user, you can find it in the 
        [account info](http://thetvdb.com/?tab=userinfo) under account identifier., 
        the language id you want to use to retrieve the info.
        """
        self._ID = id
        self.USER = user
        """Stores username if available"""
        self.USER_KEY = key
        """Stores user-key if available"""

    def _get_path(self, key):
        return self._BASE_PATH + self._URLS[key]

    def _get_id_path(self, key):
        return self._get_path(key).format(id=self._ID)

    def _get_complete_url(self, path):
        return '{base_uri}/{path}'.format(base_uri=self._BASE_URI, path=path)

    def _set_language(self, language):
        if language:
            self._headers['Accept-Language'] = language
    
    def refresh_token(self):
        """
        Refresh the current token set in the module.

        Returns the new obtained valid token for the API.
        """
        self._set_token_header()

        response = requests.request(
            'GET', self._get_complete_url('refresh_token'),
            headers=self._headers)

        response.raise_for_status()
        jsn = response.json()
        if 'token' in jsn:
            from . import KEYS
            KEYS.API_TOKEN = jsn['token']
            return KEYS.API_TOKEN
        return ''

    def _set_token_header(self, forceNew=False):
        self._headers['Authorization'] = 'Bearer ' + self.get_token(forceNew)

    def get_token(self, forceNew=False):
        """
        Get the existing token or creates it if it doesn't exist.
        Returns the API token.

        If `forceNew` is true  the function will do a new login to retrieve the token.
        """
        from . import KEYS
        if not KEYS.API_TOKEN or forceNew:
            if not KEYS.API_KEY:
                raise APIKeyError

            if hasattr(self,"USER") and hasattr(self,"USER_KEY"):
                data = {"apikey": KEYS.API_KEY, "username": self.USER, "userkey": self.USER_KEY}
            else:
                data={"apikey": KEYS.API_KEY}

            response = requests.request(
                    'POST', self._get_complete_url('login'), 
                    data=json.dumps(data), 
                    headers=self._headers)
            if response.status_code == 200:
                KEYS.API_TOKEN = response.json()['token']
            else:
                error = "Unknown error while authenticating. Check your api key or your user/userkey"
                try:
                    error = response.json()['Error']
                except:
                    pass
                raise AuthenticationError(error)
        return KEYS.API_TOKEN

    def _request(self, method, path, params=None, payload=None, forceNewToken=False, cleanJson = True):
        self._set_token_header(forceNewToken)
        
        url = self._get_complete_url(path)

        response = requests.request(
            method, url, params=params, 
            data=json.dumps(payload) if payload else payload,
            headers=self._headers)
        
        if response.status_code == 200:
            response.encoding = 'utf-8'
            jsn = response.json()
            if cleanJson and 'data' in jsn:
                return jsn['data']
            return jsn
        elif not forceNewToken:
            return self._request(method=method, path=path, params=params, payload=payload, forceNewToken=True)
        try:
            raise Exception(response.json()['Error'])
        except:
            response.raise_for_status()

    def _GET(self, path, params=None, cleanJson = True):
        return self._request('GET', path, params=params, cleanJson=cleanJson)

    def _POST(self, path, params=None, payload=None, cleanJson = True):
        return self._request('POST', path, params=params, payload=payload, cleanJson=cleanJson)

    def _DELETE(self, path, params=None, payload=None, cleanJson = True):
        return self._request('DELETE', path, params=params, payload=payload, cleanJson=cleanJson)

    def _PUT(self, path, params=None, payload=None, cleanJson = True):
        return self._request('PUT', path, params=params, payload=payload, cleanJson=cleanJson)

    def _set_attrs_to_values(self, response={}):
        """
        Set attributes to dictionary values.

        - e.g.
        >>> import tvdbsimple as tvdb
        >>> show = tmdb.Tv(10332)
        >>> response = show.info()
        >>> show.title  # instead of response['title']
        """
        if isinstance(response, dict):
            for key in response:
                setattr(self, key, response[key])