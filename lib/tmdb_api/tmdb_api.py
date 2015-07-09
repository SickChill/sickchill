"""
tmdbsimple.py is a wrapper for The Movie Database API.
Refer to the official API documentation for more information.
http://docs.themoviedb.apiary.io/

Created by Celia Oakley on 2013-10-31.
"""

import json
import requests

class TMDB:
    def __init__(self, api_key, version=3):
        TMDB.api_key = str(api_key)
        TMDB.url = 'https://api.themoviedb.org' + '/' + str(version)

    @staticmethod
    def _request(method, path, params={}, json_body={}):
        url = TMDB.url + '/' + path + '?api_key=' + TMDB.api_key
        if method == 'GET':
            headers = {'Accept': 'application/json'}
            content = requests.get(url, params=params, headers=headers).content
        elif method == 'POST':
            for key in params.keys():
                url += '&' + key + '=' + params[key]
            headers = {'Content-Type': 'application/json', \
                       'Accept': 'application/json'}
            content = requests.post(url, data=json.dumps(json_body), \
                                    headers=headers).content
        elif method == 'DELETE':
            for key in params.keys():
                url += '&' + key + '=' + params[key]
            headers = {'Content-Type': 'application/json', \
                       'Accept': 'application/json'}
            content = requests.delete(url, data=json.dumps(json_body), \
                                    headers=headers).content
        else:
            raise Exception('method: ' + method + ' not supported.')
        response = json.loads(content.decode('utf-8'))
        return response
    
    #
    # Set attributes to dictionary values.
    # - e.g.
    # >>> tmdb = TMDB()
    # >>> movie = tmdb.Movie(103332)
    # >>> response = movie.info()
    # >>> movie.title  # instead of response['title']
    #
    @staticmethod
    def _set_attrs_to_values(object, response={}):
        for key in response.keys():
            setattr(object, key, response[key])

    #
    # Configuration
    # http://docs.themoviedb.apiary.io/#configuration
    #
    class Configuration:
        def __init__(self):
            pass

        def info(self):
            path = 'configuration'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Account
    # http://docs.themoviedb.apiary.io/#account
    #
    class Account:
        def __init__(self, session_id):
            self.session_id = session_id

        # need to call this first to set account id
        def info(self):
            path = 'account'
            params = {'session_id': self.session_id}
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language
        def lists(self, params={}):
            path = 'account' + '/' + str(self.session_id) + '/lists'
            params['session_id'] = self.session_id
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, sort_by, sort_order, language
        def favorite_movies(self, params={}):
            path = 'account' + '/' + str(self.session_id) + '/favorite_movies'
            params['session_id'] = self.session_id
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required JSON body: movie_id, favorite
        def favorite(self, json_body):
            path = 'account' + '/' + str(json_body['movie_id']) + '/favorite'
            params = {'session_id': self.session_id}
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, sort_by, sort_order, language
        def rated_movies(self, params={}):
            path = 'account' + '/' + str(self.session_id) + '/rated_movies'
            params['session_id'] = self.session_id
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, sort_by, sort_order, language
        def movie_watchlist(self, params={}):
            path = 'account' + '/' + str(self.session_id) + '/movie_watchlist'
            params['session_id'] = self.session_id
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # required JSON body: movie_id, movie_watchlist
        def movie_watchlist_post(self, json_body):
            path = 'account' + '/' + str(json_body['movie_id']) + \
                  '/movie_watchlist'
            params = {'session_id': self.session_id}
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Authentication
    # http://docs.themoviedb.apiary.io/#authentication
    #
    # Note: to use authentication to access a user account, see:
    #   https://www.themoviedb.org/documentation/api/sessions
    #
    class Authentication:
        def __init__(self):
            pass

        def token_new(self):
            path = 'authentication/token/new'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: request_token
        def session_new(self, params):
            path = 'authentication/session/new'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def guest_session_new(self):
            path = 'authentication/guest_session/new'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Changes
    # http://docs.themoviedb.apiary.io/#changes
    #
    class Changes:
        def __init__(self):
            pass

        # optional parameters: page, start_date, end_date
        def movie(self, params={}):
            path = 'movie/changes'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, start_date, end_date
        def person(self, params={}):
            path = 'person/changes'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Collections
    # http://docs.themoviedb.apiary.io/#collections
    #
    class Collections:
        def __init__(self, id):
            self.id = id

        # optional parameter: language
        def info(self, params={}):
            path = 'collection' + '/' + str(self.id)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language, include_image_language
        def images(self, params={}):
            path = 'collection' + '/' + str(self.id) + '/images'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Companies
    # http://docs.themoviedb.apiary.io/#companies
    #
    class Companies:
        def __init__(self, id=0):
            self.id = id

        def info(self):
            path = 'company' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language
        def movies(self, params={}):
            path = 'company' + '/' + str(self.id) + '/movies'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Credits
    # http://docs.themoviedb.apiary.io/#credits
    #
    class Credits:
        def __init__(self, credit_id):
            self.credit_id = credit_id

        # optional parameters: language
        def info(self, params={}):
            path = 'credit' + '/' + str(self.credit_id)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Discover
    # http://docs.themoviedb.apiary.io/#discover
    #
    class Discover:
        def __init__(self):
            pass

        # optional parameters: page, language, sort_by, include_adult, year, 
        # primary_release_year, vote_count.gte, vote_average.gte, with_genres, 
        # release_date.gte, release_date.lte, certification_country, 
        # certification.lte, with_companies
        def movie(self, params):
            path = 'discover/movie'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language, sort_by, first_air_date_year,
        # vote_count.gte, vote_average.gte, with_genres, with_networks,
        # first_air_date.gte, first_air_date.lte
        def tv(self, params):
            path = 'discover/tv'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Find
    # http://docs.themoviedb.apiary.io/#find
    #
    class Find:
        def __init__(self, id=0):
            self.id = id

        # required parameters: external_source
        def info(self, params={}):
            path = 'find' + '/' + str(self.id)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Genres
    # http://docs.themoviedb.apiary.io/#genres
    #
    class Genres:
        def __init__(self, id=0):
            self.id = id

        # optional parameters: language
        def list(self, params={}):
            path = 'genre/list'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language, include_all_movies, include_adult
        def movies(self, params={}):
            path = 'genre' + '/' + str(self.id) + '/movies'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Jobs
    # http://docs.themoviedb.apiary.io/#jobs
    #
    class Jobs:
        def __init__(self):
            pass

        def list(self):
            path = 'job/list'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response
            
    #
    # Keywords
    # http://docs.themoviedb.apiary.io/#keywords
    #
    class Keywords:
        def __init__(self, id):
            self.id = id

        def info(self):
            path = 'keyword' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language
        def movies(self, params={}):
            path = 'keyword' + '/' + str(self.id) + '/movies'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Lists
    # http://docs.themoviedb.apiary.io/#lists
    #
    class Lists:
        def __init__(self, id=0, session_id=0):
            self.id = id
            self.session_id = session_id

        def info(self):
            path = 'list' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: movie_id
        def item_status(self, params):
            path = 'list' + '/' + str(self.id) + '/item_status'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required JSON body: name, description
        # optional JSON body: language
        def create_list(self, json_body):
            path = 'list'
            params = {'session_id': self.session_id}
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required JSON body: media_id
        def add_item(self, json_body):
            path = 'list' + '/' + str(self.id) + '/add_item'
            params = {'session_id': self.session_id}
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # required JSON body: media_id
        def remove_item(self, json_body):
            path = 'list' + '/' + str(self.id) + '/remove_item'
            params = {'session_id': self.session_id}
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response

        def delete_list(self):
            path = 'list' + '/' + str(self.id)
            params = {'session_id': self.session_id}
            response = TMDB._request('DELETE', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Movies
    # http://docs.themoviedb.apiary.io/#movies
    #
    class Movies:
        """ """
        def __init__(self, id=0):
            self.id = id

        # optional parameters: language
        def info(self, params={}):
            path = 'movie' + '/' + str(self.id)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: country
        def alternative_titles(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/alternative_titles'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def credits(self):
            path = 'movie' + '/' + str(self.id) + '/credits'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language, include_image_language
        def images(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/images'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def keywords(self):
            path = 'movie' + '/' + str(self.id) + '/keywords'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        def releases(self):
            path = 'movie' + '/' + str(self.id) + '/releases'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        def trailers(self):
            path = 'movie' + '/' + str(self.id) + '/trailers'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        def translations(self):
            path = 'movie' + '/' + str(self.id) + '/translations'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language
        def similar_movies(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/similar_movies'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language
        def reviews(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/reviews'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language
        def lists(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/lists'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: start_date, end_date
        def changes(self, params={}):
            path = 'movie' + '/' + str(self.id) + '/changes'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def latest(self):
            path = 'movie/latest'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language
        def upcoming(self, params={}):
            path = 'movie/upcoming'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language
        def now_playing(self, params={}):
            path = 'movie/now_playing'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameters: page, language
        def popular(self, params={}):
            path = 'movie/popular'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page, language
        def top_rated(self, params={}):
            path = 'movie/top_rated'
            response = TMDB._request('GET', 'movie' + '/top_rated', params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: session_id
        def account_states(self, params):
            path = 'movie' + '/' + str(self.id) + '/account_states'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: session_id or guest_session_id
        # required JSON body: value
        def rating(self, params, json_body):
            path = 'movie' + '/' + str(self.id) + '/rating'
            response = TMDB._request('POST', path, params, json_body)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Networks
    # http://docs.themoviedb.apiary.io/#networks
    #
    class Networks:
        def __init__(self, id):
            self.id = id

        def info(self):
            path = 'network' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # People
    # http://docs.themoviedb.apiary.io/#people
    #
    class People:
        def __init__(self, id=0):
            self.id = id

        def info(self):
            path = 'person' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language
        def movie_credits(self, params={}):
            path = 'person' + '/' + str(self.id) + '/movie_credits'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language
        def tv_credits(self, params={}):
            path = 'person' + '/' + str(self.id) + '/tv_credits'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language
        def combined_credits(self, params={}):
            path = 'person' + '/' + str(self.id) + '/combined_credits'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def images(self):
            path = 'person' + '/' + str(self.id) + '/images'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: start_date, end_date
        def changes(self, params={}):
            path = 'person' + '/' + str(self.id) + '/changes'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: page
        def popular(self, params={}):
            path = 'person/popular'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def latest(self):
            path = 'person/latest'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Reviews
    # http://docs.themoviedb.apiary.io/#reviews
    #
    class Reviews:
        def __init__(self, id):
            self.id = id

        def info(self):
            path = 'review' + '/' + str(self.id)
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # Search
    # http://docs.themoviedb.apiary.io/#search
    #
    class Search:
        def __init__(self):
            pass

        # required parameters: query
        # optional parameters: page, language, include_adult, year, 
        # primary_release_year, search_type
        def movie(self, params):
            path = 'search/movie'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page, language
        def collection(self, params):
            path = 'search/collection'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page, language, first_air_date_year, search_type
        def tv(self, params):
            path = 'search/tv'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page, include_adult, search_type
        def person(self, params):
            path = 'search/person'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page, include_adult
        def list(self, params):
            path = 'search/list'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page
        def company(self, params):
            path = 'search/company'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # required parameters: query
        # optional parameters: page
        def keyword(self, params):
            path = 'search/keyword'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # TV
    # http://docs.themoviedb.apiary.io/#tv
    #
    class TV:
        def __init__(self, id=0):
            self.id = id

        # optional parameter: language
        def info(self, params={}):
            path = 'tv' + '/' + str(self.id)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response
            
        # optional parameter: language
        def credits(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/credits'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: language
        def external_ids(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/external_ids'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameters: language, include_image_language
        def images(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/images'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def translations(self):
            path = 'tv' + '/' + str(self.id) + '/translations'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: page, language
        def top_rated(self, params={}):
            path = 'tv/top_rated'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: page, language
        def popular(self, params={}):
            path = 'tv/popular'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # TV Seasons
    # http://docs.themoviedb.apiary.io/#tvseasons
    #
    class TV_Seasons:
        def __init__(self, id, season_number):
            self.id = id
            self.season_number = season_number

        # optional parameter: language
        def info(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def credits(self):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/credits'
            response = TMDB._request('GET', path)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: language
        def external_ids(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/external_ids'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: language
        def images(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/images'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

    #
    # TV Episodes
    # http://docs.themoviedb.apiary.io/#tvepisodes
    #
    class TV_Episodes:
        def __init__(self, id, season_number, episode_number):
            self.id = id
            self.season_number = season_number
            self.episode_number = episode_number

        # optional parameter: language
        def info(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/episode' + \
                   '/' + str(self.episode_number)
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        def credits(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/episode' + \
                   '/' + str(self.episode_number) + '/credits'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: language
        def external_ids(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/episode' + \
                   '/' + str(self.episode_number) + '/external_ids'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

        # optional parameter: language
        def images(self, params={}):
            path = 'tv' + '/' + str(self.id) + '/season' + \
                   '/' + str(self.season_number) + '/episode' + \
                   '/' + str(self.episode_number) + '/images'
            response = TMDB._request('GET', path, params)
            TMDB._set_attrs_to_values(self, response)
            return response

