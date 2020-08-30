import datetime
import json
import logging
import threading

import tmdbsimple
from imdbpie import Imdb
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tmdbsimple import movies, search

from . import settings
from .oldbeard.databases import movie
from .oldbeard.db import db_cons, db_full_path, db_locks

logger = logging.getLogger('sickchill.movie')


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
    def search_tmdb(query=None, tmdb_id=None, year=None, language=None, adult=False):
        if tmdb_id:
            results = [movies.Movies(id=tmdb_id)]
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

    def add_from_tmdb(self, tmdb_id: str, language: str = settings.INDEXER_DEFAULT_LANGUAGE):
        logger.debug(f'Adding movie from tmdb with id: {tmdb_id}')
        existing = self.session.query(movie.IndexerData).filter_by(pk=tmdb_id).first()
        if existing:
            logger.debug(f'Movie already existed as {existing.movie.name}')
            return existing

        tmdb_object = tmdbsimple.movies.Movies(id=tmdb_id).info()
        instance = movie.Movie(tmdb_object['title'], year=tmdb_object['release_date'].split('-')[0])
        instance.date = datetime.datetime.strptime(tmdb_object['release_date'], '%Y-%m-%d').date()
        instance.tmdb_data = tmdb_object
        instance.language = language

        self.session.add(instance)

        tmdb_data = movie.IndexerData(site='tmdb', data=tmdb_object,  movie=instance, pk=tmdb_id)
        self.session.add(tmdb_data)

        self.commit()

        logger.debug(f'Returning instance for {instance.name}')
        return instance

    def add_from_imdb(self, imdb_id: str, language: str = settings.INDEXER_DEFAULT_LANGUAGE):
        logger.debug(f'Adding movie from imdb id: {imdb_id}')
        existing = self.session.query(movie.IndexerData).filter_by(pk=imdb_id).first()
        if existing:
            logger.debug(f'Movie already existed as {existing.name}')
            return existing

        imdb_object = self.imdb.get_title(imdb_id)
        instance = movie.Movie(imdb_object['base']['title'], year=imdb_object['base']['year'])
        instance.language = language

        self.session.add(instance)

        imdb_data = movie.IndexerData(site='imdb', data=imdb_object, movie=instance, pk=imdb_id)
        self.session.add(imdb_data)

        genres = self.imdb.get_title_genres(imdb_id)
        if genres:
            for genre in genres['genres']:
                genre_instance = movie.Genres(pk=genre, indexer_data=imdb_data)
                self.session.add(genre_instance)

        self.commit()

        logger.debug(f'Returning instance for {instance.name}')
        return instance

    def commit(self):
        logger.debug('Committing')
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
