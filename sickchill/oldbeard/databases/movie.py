import datetime
import logging
from typing import List

import guessit
from slugify import slugify
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

logger = logging.getLogger("sickchill.movie")


class Base(DeclarativeBase):
    """Declarative Base Class"""


Session = sessionmaker()


class Movie(Base):
    __tablename__ = "movie"
    pk: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    date: Mapped[datetime.date]
    year: Mapped[int]
    status: Mapped[int]
    paused: Mapped[bool] = mapped_column(default=False)
    location: Mapped[str]
    start: Mapped[datetime.timedelta] = mapped_column(default=datetime.timedelta(days=-7))
    interval: Mapped[datetime.timedelta] = mapped_column(default=datetime.timedelta(days=1))
    added: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated: Mapped[datetime.datetime] = mapped_column(onupdate=datetime.datetime.now)
    completed: Mapped[datetime.datetime]
    searched: Mapped[datetime.datetime]
    slug: Mapped[str]

    language: Mapped[str]

    result_pk: Mapped[int] = mapped_column(ForeignKey("result.pk"))
    results: Mapped[List["Result"]] = relationship(backref="movie")

    images: Mapped[List["Images"]] = relationship(backref="movie")
    indexer_data: Mapped[List["IndexerData"]] = relationship(backref="movie")

    def __init__(self, name: str, year: int):
        self.name = name
        self.year = year

    @property
    def poster(self):
        return ""

    def __get_named_indexer_data(self, name):
        if self.indexer_data:
            for data in self.indexer_data:
                if data.site == name:
                    return data

    @property
    def imdb_data(self):
        data = self.__get_named_indexer_data("imdb")
        if data:
            return data.data
        return dict()

    @property
    def imdb_id(self):
        data = self.__get_named_indexer_data("imdb")
        if data:
            return data.pk
        return ""

    @property
    def tmdb_id(self):
        data = self.__get_named_indexer_data("tmdb")
        if data:
            return data.pk
        return ""

    @property
    def imdb_genres(self):
        data = self.__get_named_indexer_data("imdb")
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
            logger.debug(f"We do not have data for {name}")
        except (IndexError, KeyError):
            logger.debug(f"KeyError: {name}{''.join([f'[{k}]' for k in keys])}")

    @property
    def runtime(self):
        return self.__get_indexer_values("imdb", ["base", "runningTimeInMinutes"])

    @property
    def imdb_votes(self):
        return self.__get_indexer_values("imdb", ["ratings", "ratingCount"])

    @property
    def imdb_rating(self):
        return self.__get_indexer_values("imdb", ["ratings", "rating"])

    @property
    def imdb_outline(self):
        return self.__get_indexer_values("imdb", ["plot", "outline", "text"])

    @property
    def imdb_summary(self):
        return self.__get_indexer_values("imdb", ["plot", "summaries", 0, "text"])

    @staticmethod
    def slugify(target, value, old_value, initiator):
        if value and (not target.slug or value != old_value):
            target.slug = slugify(value)

    def search_strings(self):
        return {"Movie": [f"{self.name} {self.year}"]}

    def __repr__(self):
        return f"{self.name}"


listen(Movie.name, "set", Movie.slugify, retval=False)


class Result(Base):
    __tablename__ = "result"
    pk: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    title: Mapped[str]
    url: Mapped[str]
    size: Mapped[int]
    year: Mapped[int]
    provider: Mapped[str]
    seeders: Mapped[int]
    leechers: Mapped[int]
    info_hash: Mapped[str]
    group: Mapped[str]
    kind: Mapped[str]
    guess = mapped_column(JSON)
    found: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    updated: Mapped[datetime.datetime] = mapped_column(onupdate=datetime.datetime.now)

    session = Session()

    def __init__(self, result: dict, movie: Movie, provider):
        name = result["title"]
        guess = guessit.guessit(name)
        if not (guess and guess["type"] == "movie"):
            logging.debug(f"This is an episode, not a movie: {name}")
            return

        if not self.session.query(Movie).filter(Movie.name.like(f"{guess['title']}%")).count():
            logging.debug(f"This result does not match any of our movies")
            return

        self.info_hash = result["hash"]
        self.url = result["link"]
        self.name = name
        self.title = guess["title"]
        self.group = guess["release_group"]
        self.seeders = result["seeders"]
        self.leechers = result["leechers"]
        self.size = result["size"]
        self.year = guess["year"] or movie.year
        self.kind = provider.provider_type

        self.provider = provider.get_id()

        self.guess = guess

        self.movie = movie

    def __repr__(self):
        return f"{self.name}"


class Images(Base):
    __tablename__ = "images"

    url: Mapped[str] = mapped_column(primary_key=True)
    path: Mapped[str]
    site: Mapped[str]
    style: Mapped[int]

    movie_pk: Mapped[int] = mapped_column(ForeignKey("movie.pk"))

    def __init__(self, site: str, movie_pk: int, url: str, path: str, style: int):
        self.url = url
        self.path = path
        self.site = site
        self.style = style
        self.movie_pk = movie_pk


class IndexerData(Base):
    __tablename__ = "indexer_data"
    pk: Mapped[str] = mapped_column(primary_key=True)
    site: Mapped[str]
    data = mapped_column(JSON)

    movie_pk: Mapped[int] = mapped_column(ForeignKey("movie.pk"))

    genres: Mapped[List["Genres"]] = relationship(backref="indexer_data")

    def __repr__(self):
        return f"[{self.__tablename__.replace('_', ' ').title()}] {self.site}: {self.pk} - {self.movie.name}"


class Genres(Base):
    __tablename__ = "genres"
    pk: Mapped[str] = mapped_column(primary_key=True)
    indexer_data_pk: Mapped[int] = mapped_column(ForeignKey("indexer_data.pk"))
