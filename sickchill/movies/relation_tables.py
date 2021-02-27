from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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
