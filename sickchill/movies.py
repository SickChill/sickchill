import threading

import tmdbsimple
from imdbpie import Imdb
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tmdbsimple import movies, search

from . import settings
from .oldbeard.databases import movie
from .oldbeard.db import db_cons, db_full_path, db_locks


class MovieList:
    def __init__(self):
        tmdbsimple.API_KEY = settings.TMDB_API_KEY

        self.filename = "movies.db"
        self.full_path = db_full_path(self.filename)

        if self.filename not in db_cons or not db_cons[self.filename]:
            movie.Session.configure(bind=create_engine(f"sqlite:///{self.full_path}", echo=True))
            self.session: Session = movie.Session()
            movie.Base.metadata.create_all(self.session.bind, checkfirst=True)

            db_locks[self.filename] = threading.Lock()
            db_cons[self.filename] = self.session
        else:
            self.session: Session = db_cons[self.filename]

        self.imdb = Imdb(exclude_episodes=True)

    @staticmethod
    def search_tmdb(query=None, tmdbid=None, year=None, language=None, adult=False):
        if tmdbid:
            results = [movies.Movies(id=tmdbid)]
        elif query:
            tmdb_kwargs = dict(query=query, year=year, language=language, adult=adult)
            tmdb_kwargs = {key: value for key, value in tmdb_kwargs.items() if value}
            results = search.Search().movie(**tmdb_kwargs)['results']
        else:
            raise Exception('Query or tmdb id is required!')

        return results

    def __discover_tmdb(self, language=None, type='latest'):
        tmdb_kwargs = dict(language=language) if language else dict()
        return getattr(movies.Movies(), type)(**tmdb_kwargs)['results']

    def popular_tmdb(self, language=None):
        return self.__discover_tmdb(language, 'popular')

    def recommended_tmdb(self, language=None):
        return self.__discover_tmdb(language, 'recommendations')

    def search_imdb(self, query: str = ''):
        return self.imdb.search_for_title(title=query)

    def popular_imdb(self):
        return self.imdb.get_popular_movies()

    def add(self, **kwargs):
        # instance = movie.Movie()
        # self.session.add(instance)
        pass

    def delete(self, pk):
        instance = self.session.query(movie.Movie).get(pk)
        if instance:
            self.session.delete(instance)
