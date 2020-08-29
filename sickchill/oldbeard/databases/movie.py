import datetime
import logging

import guessit
from slugify import slugify
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Interval, JSON, SmallInteger, String
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

logger = logging.getLogger('sickchill.movie')

Base = declarative_base()
Session = sessionmaker()


class Movie(Base):
    __tablename__ = "movie"
    pk = Column(Integer, primary_key=True)
    name = Column(String)
    date = Column(Date)
    year = Column(SmallInteger)
    status = Column(Integer)
    paused = Column(Boolean, default=False)
    location = Column(String)
    start = Column(Interval, default=datetime.timedelta(days=-7))
    interval = Column(Interval, default=datetime.timedelta(days=1))
    added = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    completed = Column(DateTime)
    searched = Column(DateTime)
    slug = Column(String)
    imdb_data = Column(JSON)
    tmdb_data = Column(JSON)
    omdb_data = Column(JSON)

    language = Column(String)

    result = relationship("Result", uselist=False, back_populates="movie")
    results = relationship("Result", back_populates="movie")

    external_ids = relationship("ExternalID", back_populates="movie")
    images = relationship("Images", back_populates="movie")

    def __init__(self, name: str, year: int):
        self.name = name
        self.year = year

    @property
    def poster(self):
        return ''

    @property
    def imdb_id(self):
        if self.external_ids:
            return self.external_ids['imdb']
        return ''

    @staticmethod
    def slugify(target, value, old_value, initiator):
        if value and (not target.slug or value != old_value):
            target.slug = slugify(value)

    def __repr__(self):
        return f"{self.name}"


listen(Movie.name, 'set', Movie.slugify, retval=False)


class Result(Base):
    __tablename__ = "result"
    pk = Column(Integer, primary_key=True)
    name = Column(String)
    title = Column(String)
    url = Column(String)
    size = Column(Integer)
    year = Column(SmallInteger)
    provider = Column(String)
    seeders = Column(Integer)
    leechers = Column(Integer)
    group = Column(String)
    type = Column(String)
    found = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)

    movie_pk = Column(Integer, ForeignKey('movie.pk'))
    movie = relationship("Movie", back_populates="result")

    session = Session()

    def __init__(self, name: str, url: str, seeders: int, leechers: int, size: int, type=None):
        guess = guessit.guessit(name)
        if not (guess and guess["type"] == "movie"):
            logging.debug(f"This is an episode, not a movie: {name}")
            return

        if not self.session.query(Movie).filter(Movie.name.like(f"{guess['title']}%")).count():
            logging.debug(f"This result does not match any of our movies")
            return

        if not type:
            if url.startswith('magnet') or url.endswith('.torrent'):
                type = 'torrent'
            elif url.endswith('.nzb'):
                type = 'nzb'
            else:
                logging.debug(f"Cannot determine the type of download for {url}")
                return

        self.url = url
        self.name = name
        self.title = guess["title"]
        self.group = guess["release_group"]
        self.seeders = seeders
        self.leechers = leechers
        self.size = size
        self.year = guess["year"]
        self.type = type

    def __repr__(self):
        return f"{self.name}"


class ExternalID(Base):
    __tablename__ = "external_id"
    pk = Column(String, primary_key=True)
    site = Column(String)

    movie_pk = Column(Integer, ForeignKey('movie.pk'))
    movie = relationship("Movie", back_populates="external_ids")

    def __init__(self, site: str, movie_pk: int, pk: str):
        self.pk = pk
        self.site = site
        self.movie_pk = movie_pk


class Images(Base):
    __tablename__ = 'images'

    url = Column(String, primary_key=True)
    path = Column(String)
    site = Column(String)
    style = Column(Integer)

    movie_pk = Column(Integer, ForeignKey('movie.pk'))
    movie = relationship("Movie", back_populates="images")

    def __init__(self, site: str, movie_pk: int, url: str, path: str, style: int):
        self.url = url
        self.path = path
        self.site = site
        self.style = style
        self.movie_pk = movie_pk
