import json
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
            movie.Session.configure(
                bind=create_engine(
                    f"sqlite:///{self.full_path}",
                    echo=True,
                    connect_args={"check_same_thread": False},
                    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
                )
            )
            self.session: Session = movie.Session()
            movie.Base.metadata.create_all(self.session.bind, checkfirst=True)

            db_locks[self.filename] = threading.Lock()
            db_cons[self.filename] = self.session
        else:
            self.session: Session = db_cons[self.filename]

        self.imdb = Imdb(exclude_episodes=True)

    def __iter__(self):
        for item in self.query.all():
            yield item

    def __getitem__(self, pk):
        return self.query.get(pk)

    def __contains__(self, pk):
        return bool(self.get(pk, False))

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

    def popular_tmdb(self, language=None):
        tmdb_kwargs = dict(language=language) if language else dict()
        return movies.Movies().popular(**tmdb_kwargs)['results']

    def search_imdb(self, query: str = ''):
        return self.imdb.search_for_title(title=query)

    def popular_imdb(self):
        return self.imdb.get_popular_movies()['ranks']

    def add_from_imdb(self, imdb_id: str, language: str = settings.INDEXER_DEFAULT_LANGUAGE):
        existing = self.session.query(movie.ExternalID).filter_by(pk=imdb_id).first()
        if existing:
            return existing

        imdb_object = self.imdb.get_title(imdb_id)
        instance = movie.Movie(imdb_object['base']['title'], year=imdb_object['base']['year'])
        instance.imdb_data = imdb_object
        instance.language = language

        self.session.add(instance)
        external_id = movie.ExternalID(pk=imdb_id, movie_pk=instance.pk, site='imdb')
        self.session.add(external_id)

        self.commit()

        return movie

    def commit(self):
        self.session.flush()
        self.session.commit()

    def delete(self, pk):
        instance = self.query.get(pk)
        if instance:
            self.session.delete(instance)

    @property
    def query(self):
        return self.session.query(movie.Movie)

    def by_slug(self, slug):
        return self.query.filter_by(slug=slug).first()
