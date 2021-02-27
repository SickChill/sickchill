import datetime
import logging

import guessit
from slugify import slugify
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Interval, JSON, SmallInteger, Unicode
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .relation_tables import (indexer_data_genres_table, movies_groups_table, movies_qualities_table, qualities_codecs_table, qualities_resolutions_table,
                              qualities_sources_table)
from .types import ChoiceType, DesireTypes, HistoryActions, ImageTypes, IMDB, IndexerNames, PathType, RegexType, TMDB

logger = logging.getLogger('sickchill.movies')

Session = sessionmaker()
Base = declarative_base()


class Timestamp:
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)


class Movies(Base, Timestamp):
    __tablename__ = "movies"
    pk = Column(Integer, primary_key=True)
    name = Column(Unicode)
    date = Column(Date)
    year = Column(SmallInteger)
    status = Column(Integer)
    paused = Column(Boolean, default=False)
    location = Column(PathType)
    start = Column(Interval, default=datetime.timedelta(days=-7))
    interval = Column(Interval, default=datetime.timedelta(days=1))
    completed = Column(DateTime, nullable=True, default=None)
    processed = Column(DateTime, nullable=True, default=None)
    searched = Column(DateTime, nullable=True, default=None)
    slug = Column(Unicode)

    roots_pk = Column(Integer, ForeignKey('roots.name'))

    qualities = relationship("Qualities", secondary=movies_qualities_table, backref='movies')
    groups = relationship("Groups", secondary=movies_groups_table, backref='movies')

    language = Column(Unicode)

    results: list = relationship("Result", backref='movie')

    images: list = relationship("Images", backref='movie')
    indexer_data: list = relationship("IndexerData", backref='movie')

    def __init__(self, name: str, year: int):
        self.name = name
        self.year = year

    @property
    def poster(self):
        return ''

    def __get_named_indexer_data(self, name):
        if self.indexer_data:
            for data in self.indexer_data:
                if data.site == IndexerNames[name]:
                    return data

    @property
    def imdb_data(self):
        data = self.__get_named_indexer_data(IMDB)
        if data:
            return data.data
        return dict()

    @property
    def imdb_id(self):
        data = self.__get_named_indexer_data(IMDB)
        if data:
            return data.code
        return ''

    @property
    def tmdb_id(self):
        data = self.__get_named_indexer_data(TMDB)
        if data:
            return data.code
        return ''

    @property
    def imdb_genres(self):
        data = self.__get_named_indexer_data(IMDB)
        if data:
            return data.genres
        return []

    def __get_indexer_values(self, name, keys: list):
        try:
            data = getattr(self, f"{name}_data")
            for key in keys:
                data = data[key]
            return data
        except AttributeError:
            logger.debug(f'We do not have data for {name}')
        except (IndexError, KeyError):
            logger.debug(f"KeyError: {name}{''.join([f'[{k}]' for k in keys])}")

    @property
    def runtime(self):
        return self.__get_indexer_values('imdb', ['base', 'runningTimeInMinutes'])

    @property
    def imdb_votes(self):
        return self.__get_indexer_values('imdb', ['ratings', 'ratingCount'])

    @property
    def imdb_rating(self):
        return self.__get_indexer_values('imdb', ['ratings', 'rating'])

    @property
    def imdb_outline(self):
        return self.__get_indexer_values('imdb', ['plot', 'outline', 'text'])

    @property
    def imdb_summary(self):
        return self.__get_indexer_values('imdb', ['plot', 'summaries', 0, 'text'])

    @staticmethod
    def slugify(target, value, old_value, _initiator):
        if value and (not target.slug or value != old_value):
            target.slug = slugify(value)

    def search_strings(self):
        return {'Movie': [f"{self.name} {self.year}"]}

    def __repr__(self):
        return f"{self.name}"


listen(Movies.name, 'set', Movies.slugify, retval=False)


class Results(Base, Timestamp):
    __tablename__ = "results"
    name = Column(Unicode, primary_key=True)
    title = Column(Unicode)
    url = Column(Unicode)
    size = Column(Integer)
    year = Column(SmallInteger)
    provider = Column(Unicode)
    seeders = Column(Integer)
    leechers = Column(Integer)
    info_hash = Column(Unicode)
    group = Column(Unicode)
    type = Column(Unicode)
    guess = Column(JSON)

    current = Column(Boolean, default=False)

    movies_pk = Column(Integer, ForeignKey('movies.pk'))

    session = Session()

    def __init__(self, result: dict, movie: Movies, provider):
        name = result['title']
        guess = guessit.guessit(name)
        if not guess:
            logger.debug(f"Unable to determine a credible guess for {name}")
            return

        if guess["type"] != "movie":
            logger.debug(f"This is an episode, not a movie: {name}")
            return

        if not movie.name.startswith(guess['title']):
            if not self.session.query(Movies).filter(Movies.name.like(f"{guess['title']}%")).count():
                logger.debug(f"This result does not match any of our movies")
                return

        # if guess['year'] != movie.year:
        #     logger.debug(f"This result has a year that does not match our movie: {guess['year']}")
        #     return

        self.info_hash = result['hash']
        self.url = result['link']
        self.name = name
        self.title = guess["title"]
        self.group = guess["release_group"]
        self.seeders = result['seeders']
        self.leechers = result['leechers']
        self.size = result['size']
        self.year = guess["year"] or movie.year
        self.type = provider.provider_type

        self.provider = provider.get_id()

        self.guess = guess

        self.movie = movie

        self.session.add(self)
        self.session.flush()
        self.session.commit()

    def __repr__(self):
        return f"{self.name}"


class Images(Base, Timestamp):
    __tablename__ = 'images'

    url = Column(Unicode, primary_key=True)
    path = Column(PathType, unique=True)
    site = Column(ChoiceType(IndexerNames))
    style = Column(ChoiceType(ImageTypes))

    movies_pk = Column(Integer, ForeignKey('movies.pk'))

    def __init__(self, site: str, movies_pk: int, url: str, path: str, style: int):
        self.url = url
        self.path = path
        self.site = site
        self.style = style
        self.movies_pk = movies_pk


class IndexerData(Base, Timestamp):
    __tablename__ = 'indexer_data'
    pk = Column(Integer, primary_key=True)
    code = Column(Integer)
    prefix = Column(Unicode)
    site = Column(ChoiceType(IndexerNames))
    data = Column(JSON)

    genres: list = relationship('Genres', secondary=indexer_data_genres_table, backref='indexer_data')

    movies_pk = Column(Integer, ForeignKey('movies.pk'))

    def __repr__(self):
        return f"[{self.__tablename__.replace('_', ' ').title()}] {self.site}: {self.pk} - {self.movie.name}"


class Genres(Base):
    __tablename__ = 'genres'
    name = Column(Unicode, primary_key=True)
    description = Column(Unicode)


class Groups(Base):
    __tablename__ = 'groups'
    name = Column(Unicode, primary_key=True)
    status = Column(ChoiceType(DesireTypes))
    default = Column(Boolean, default=False)


class Qualities(Base):
    __tablename__ = 'qualities'
    name = Column(Unicode, unique=True, primary_key=True)
    min_size = Column(Integer)
    max_size = Column(Integer)
    weight = Column(Integer, unique=True, nullable=False)
    default = Column(Boolean, default=False, nullable=False)
    status = Column(ChoiceType(DesireTypes))

    resolutions = relationship('Resolutions', secondary=qualities_resolutions_table, backref='qualities')
    sources = relationship('Sources', secondary=qualities_sources_table, backref='qualities')
    codecs = relationship('Codecs', secondary=qualities_codecs_table, backref='qualities')

    # @staticmethod
    # def default_data(target, connection, **kw):
    #     connection.execute(target.insert(), {'pk': 1, 'name': 'HDWEB-DL'}, {'pk': 2, 'name': 'FULLHD-WEBDL'})


# event.listen(Qualities.__table__, 'after_create', Qualities.default_data)


class Resolutions(Base):
    __tablename__ = 'resolutions'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)


class Sources(Base):
    __tablename__ = 'sources'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)


class Codecs(Base):
    __tablename__ = 'codecs'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)


class Roots(Base, Timestamp):
    __tablename__ = 'roots'
    name = Column(Unicode, primary_key=True)
    path = Column(PathType, unique=True, nullable=False)
    default = Column(Boolean, default=False, nullable=False)

    movies = relationship('Movies', backref='root')


class History(Base, Timestamp):
    __tablename__ = 'history'
    pk = Column(Integer, primary_key=True)
    action = Column(ChoiceType(HistoryActions), nullable=False)
    item = None  # Fixme
