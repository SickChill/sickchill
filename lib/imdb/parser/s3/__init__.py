# -*- coding: utf-8 -*-
"""
parser.s3 package (imdb package).

This package provides the IMDbS3AccessSystem class used to access
IMDb's data through the web interface.
the imdb.IMDb function will return an instance of this class when
called with the 'accessSystem' argument set to "s3" or "s3dataset".

Copyright 2017-2018 Davide Alberani <da@erlug.linux.it>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import logging
import sqlalchemy
from imdb import IMDbBase
from .utils import DB_TRANSFORM, title_soundex, name_soundexes, scan_titles, scan_names

from imdb.Movie import Movie
from imdb.Person import Person


class IMDbS3AccessSystem(IMDbBase):
    """The class used to access IMDb's data through the s3 dataset."""

    accessSystem = 's3'
    _s3_logger = logging.getLogger('imdbpy.parser.s3')
    _metadata = sqlalchemy.MetaData()

    def __init__(self, uri, adultSearch=True, *arguments, **keywords):
        """Initialize the access system."""
        IMDbBase.__init__(self, *arguments, **keywords)
        self._engine = sqlalchemy.create_engine(uri, echo=False)
        self._metadata.bind = self._engine
        self._metadata.reflect()
        self.T = self._metadata.tables

    def _rename(self, table, data):
        for column, conf in DB_TRANSFORM.get(table, {}).items():
            if 'rename' not in conf:
                continue
            if column not in data:
                continue
            data[conf['rename']] = data[column]
            del data[column]
        return data

    def _clean(self, data, keys_to_remove=None):
        if keys_to_remove is None:
            keys_to_remove = []
        for key in list(data.keys()):
            if key in keys_to_remove or data[key] in (None, '', []):
                del data[key]
        return data

    def _base_title_info(self, movieID, movies_cache=None, persons_cache=None):
        if movies_cache is None:
            movies_cache = {}
        if persons_cache is None:
            persons_cache = {}
        if movieID in movies_cache:
            return movies_cache[movieID]
        tb = self.T['title_basics']
        movie = tb.select(tb.c.tconst == movieID).execute().fetchone() or {}
        data = self._rename('title_basics', dict(movie))
        data['year'] = str(data.get('startYear') or '')
        if 'endYear' in data and data['endYear']:
            data['year'] += '-%s' % data['endYear']
        genres = data.get('genres') or ''
        data['genres'] = genres.lower().split(',')
        if 'runtimes' in data and data['runtimes']:
            data['runtimes'] = [data['runtimes']]
        self._clean(data, ('startYear', 'endYear', 'movieID'))
        movies_cache[movieID] = data
        return data

    def _base_person_info(self, personID, movies_cache=None, persons_cache=None):
        if movies_cache is None:
            movies_cache = {}
        if persons_cache is None:
            persons_cache = {}
        if personID in persons_cache:
            return persons_cache[personID]
        nb = self.T['name_basics']
        person = nb.select(nb.c.nconst == personID).execute().fetchone() or {}
        data = self._rename('name_basics', dict(person))
        movies = []
        for movieID in (data.get('known for') or '').split(','):
            movieID = int(movieID)
            movie_data = self._base_title_info(movieID, movies_cache=movies_cache, persons_cache=persons_cache)
            movie = Movie(movieID=movieID, data=movie_data, accessSystem=self.accessSystem)
            movies.append(movie)
        data['known for'] = movies
        self._clean(data, ('ns_soundex', 'sn_soundex', 's_soundex', 'personID'))
        persons_cache[personID] = data
        return data

    def get_movie_main(self, movieID):
        movieID = int(movieID)
        data = self._base_title_info(movieID)
        _movies_cache = {movieID: data}
        _persons_cache = {}

        tc = self.T['title_crew']
        movie = tc.select(tc.c.tconst == movieID).execute().fetchone() or {}
        tc_data = self._rename('title_crew', dict(movie))
        writers = []
        directors = []
        for key, target in (('director', directors), ('writer', writers)):
            for personID in (tc_data.get(key) or '').split(','):
                personID = int(personID)
                person_data = self._base_person_info(personID,
                                                     movies_cache=_movies_cache,
                                                     persons_cache=_persons_cache)
                person = Person(personID=personID, data=person_data, accessSystem=self.accessSystem)
                target.append(person)
        tc_data['director'] = directors
        tc_data['writer'] = writers
        data.update(tc_data)

        te = self.T['title_episode']
        movie = tc.select(te.c.tconst == movieID).execute().fetchone() or {}
        te_data = self._rename('title_episode', dict(movie))
        if 'parentTconst' in te_data:
            te_data['episodes of'] = self._base_title_info(te_data['parentTconst'])
        self._clean(te_data, ('parentTconst',))
        data.update(te_data)

        tp = self.T['title_principals']
        movie = tp.select(tp.c.tconst == movieID).execute().fetchone() or {}
        tp_data = self._rename('title_principals', dict(movie))
        cast = []
        for personID in (tp_data.get('cast') or '').split(','):
            personID = int(personID)
            person_data = self._base_person_info(personID,
                                                    movies_cache=_movies_cache,
                                                    persons_cache=_persons_cache)
            person = Person(personID=personID, data=person_data, accessSystem=self.accessSystem)
            cast.append(person)
        tp_data['cast'] = cast
        data.update(tp_data)

        tr = self.T['title_ratings']
        movie = tr.select(tr.c.tconst == movieID).execute().fetchone() or {}
        tr_data = self._rename('title_ratings', dict(movie))
        data.update(tr_data)

        self._clean(data, ('movieID', 't_soundex'))
        return {'data': data, 'infosets': self.get_movie_infoset()}

    # we don't really have plot information, yet
    get_movie_plot = get_movie_main

    def get_person_main(self, personID):
        personID = int(personID)
        data = self._base_person_info(personID)
        self._clean(data, ('personID',))
        return {'data': data, 'infosets': self.get_person_infoset()}

    get_person_filmography = get_person_main
    get_person_biography = get_person_main

    def _search_movie(self, title, results, _episodes=False):
        title = title.strip()
        if not title:
            return []
        results = []
        t_soundex = title_soundex(title)
        tb = self.T['title_basics']
        conditions = [tb.c.t_soundex == t_soundex]
        if _episodes:
            conditions.append(tb.c.titleType == 'episode')
        results = tb.select(sqlalchemy.and_(*conditions)).execute().fetchall()
        results = [(x['tconst'], self._clean(self._rename('title_basics', dict(x)), ('t_soundex',)))
                   for x in results]
        results = scan_titles(results, title)
        results = [x[1] for x in results]
        return results

    def _search_episode(self, title, results):
        return self._search_movie(title, results=results, _episodes=True)

    def _search_person(self, name, results):
        name = name.strip()
        if not name:
            return []
        results = []
        ns_soundex, sn_soundex, s_soundex = name_soundexes(name)
        nb = self.T['name_basics']
        conditions = [nb.c.ns_soundex == ns_soundex]
        if sn_soundex:
            conditions.append(nb.c.sn_soundex == sn_soundex)
        if s_soundex:
            conditions.append(nb.c.s_soundex == s_soundex)
        results = nb.select(sqlalchemy.or_(*conditions)).execute().fetchall()
        results = [(x['nconst'], self._clean(self._rename('name_basics', dict(x)),
                                             ('ns_soundex', 'sn_soundex', 's_soundex')))
                   for x in results]
        results = scan_names(results, name)
        results = [x[1] for x in results]
        return results

