import datetime
import logging
import re

import guessit
from slugify import slugify
from sqlalchemy import Boolean, Column, Date, DateTime, event, ForeignKey, Integer, Interval, JSON, SmallInteger, Table, Unicode
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from .types import ChoiceType, DesireTypes, HistoryActions, ImageTypes, IMDB, IndexerNames, PathType, RegexType, ReleaseTypeNames, TMDB
from .utils import reverse_key

logger = logging.getLogger('sickchill.movies')

Session = sessionmaker()
Base = declarative_base()


class Timestamp:
    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)


movies_qualities_table = Table(
    'movies_qualities', Base.metadata,
    Column('movies_pk', Integer, ForeignKey('movies.pk')),
    Column('qualities_name', Integer, ForeignKey('qualities.name'))
)

movies_groups_table = Table(
    'movies_groups', Base.metadata,
    Column('movies_pk', Integer, ForeignKey('movies.pk')),
    Column('groups_name', Integer, ForeignKey('groups.name'))
)

indexer_data_genres_table = Table(
    'indexer_data_genres', Base.metadata,
    Column('indexer_data_pk', Integer, ForeignKey('indexer_data.pk')),
    Column('genres_name', Integer, ForeignKey('genres.name'))
)

qualities_resolutions_table = Table(
    'qualities_resolutions', Base.metadata,
    Column('qualities_name', Integer, ForeignKey('qualities.name')),
    Column('resolutions_name', Integer, ForeignKey('resolutions.name'))
)

qualities_sources_table = Table(
    'qualities_sources', Base.metadata,
    Column('qualities_name', Integer, ForeignKey('qualities.name')),
    Column('sources_name', Integer, ForeignKey('sources.name'))
)

qualities_codecs_table = Table(
    'qualities_codecs', Base.metadata,
    Column('qualities_name', Integer, ForeignKey('qualities.name')),
    Column('codecs_name', Integer, ForeignKey('codecs.name'))
)

qualities_release_types_table = Table(
    'qualities_release_types', Base.metadata,
    Column('qualities_name', Integer, ForeignKey('qualities.name')),
    Column('release_types_value', Integer, ForeignKey('release_types.value'))
)


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

    results: list = relationship("Results", backref='movie')

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

    release_type_pk = Column(Integer, ForeignKey('release_types.value'))

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
    release_types = relationship('ReleaseTypes', secondary=qualities_release_types_table, backref='qualities')

    @staticmethod
    def default_data(target, session, **kw):
        # no event for this one, called directly after create_all
        pass


class Resolutions(Base):
    __tablename__ = 'resolutions'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)

    @staticmethod
    def default_data(target, connection, **kw):
        connection.execute(
            target.insert(),
            dict(name='720p', regex=r'\.720p?\.'),
            dict(name='1080p', regex=r'\.1080p?\.'),
            dict(name='1080i', regex=r'\.1080i\.'),
            dict(name='4k', regex=r'\.4k\.'),
            dict(name='8k', regex=r'\.8k\.'),
            dict(name='2160p', regex=r'\.2160p?\.'),
            dict(name='UltraHD', regex=r'\.UltraHD\.'),
            dict(name='10bit', regex=r'\.10-?bit\.'),
            dict(name='HEVC', regex=r'\.HEVC\.')
        )


class Sources(Base):
    __tablename__ = 'sources'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)

    @staticmethod
    def default_data(target, connection, **kw):
        connection.execute(
            target.insert(),
            dict(name='HDTV', regex=r'HDTV'),
            dict(name='WEB', regex='WEB'),
            dict(name='Bluray', regex='Blu-?ray')
        )


class Codecs(Base):
    __tablename__ = 'codecs'
    name = Column(Unicode, primary_key=True)
    regex = Column(RegexType, unique=True, nullable=False)

    @staticmethod
    def default_data(target, connection, **kw):
        connection.execute(
            target.insert(),
            dict(name='x264', regex=r'x264'),
            dict(name='H264', regex=r'H.?264'),
            dict(name='x265', regex='x265'),
            dict(name='XViD', regex='xvid'),
            dict(name='divx', regex='divx')
        )


class ReleaseTypes(Base):
    __tablename__ = 'release_types'
    value = Column(Integer, primary_key=True)
    results = relationship('Results', backref='release_type')

    @property
    def name(self):
        # Do not store name in the DB, because it may change with language switching.
        return reverse_key(ReleaseTypeNames, self.value)

    @staticmethod
    def default_data(target, connection, **kw):
        for value in ReleaseTypeNames.values():
            connection.execute(target.insert(), {'value': value})


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

