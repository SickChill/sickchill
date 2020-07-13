# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re

from dateutil.parser import parse

from .imdbpie import Imdb
from .objects import (
    Title, TitleEpisodes, Name, TitleName, Image, TitleRelease,
    TitleSearchResult, NameSearchResult,
)

REGEX_IMDB_ID = re.compile(r'([a-zA-Z]{2}[0-9]{7})')


class ImdbFacade(object):

    def __init__(self, client=None):
        self._client = client or Imdb()

    def get_title(self, imdb_id):
        title_data, title_aux_data = self._get_title_data(imdb_id=imdb_id)
        try:
            runtime = title_aux_data['runningTimes'][0]['timeMinutes']
        except (KeyError, IndexError):
            runtime = None
        try:
            episodes = TitleEpisodes(facade=self, imdb_id=imdb_id)
        except LookupError:
            episodes = ()
        try:
            season = title_aux_data['season']
            episode = title_aux_data['episode']
        except KeyError:
            season = None
            episode = None
        return Title(
            season=season, episode=episode, episodes=episodes,
            runtime=runtime, **title_data
        )

    def get_name(self, imdb_id):
        name_data = self._client.get_name(imdb_id=imdb_id)
        name = name_data['base']['name']
        imdb_id = self._parse_id(name_data['base']['id'])

        try:
            image_data = name_data['base']['image']
            image = Image(
                url=image_data['url'],
                height=image_data['height'],
                width=image_data['width'],
            )
        except KeyError:
            image = None

        gender = name_data['base']['gender'].lower()
        date_of_birth = parse(name_data['base']['birthDate']).date()
        birth_place = name_data['base']['birthPlace']
        try:
            bios = tuple(b['text'] for b in name_data['base']['miniBios'])
        except KeyError:
            bios = ()

        filmography_data = self._client.get_name_filmography(imdb_id)
        filmography = tuple(
            self._parse_id(f['id']) for f in filmography_data['filmography']
        )
        return Name(
            name=name, imdb_id=imdb_id, date_of_birth=date_of_birth,
            gender=gender, birth_place=birth_place, bios=bios, image=image,
            filmography=filmography,
        )

    def search_for_name(self, query):
        results = []
        for result in self._client.search_for_name(query):
            result = NameSearchResult(
                imdb_id=result['imdb_id'], name=result['name'],
            )
            results.append(result)
        return tuple(results)

    def search_for_title(self, query):
        results = []
        for result in self._client.search_for_title(query):
            if result['year']:
                year = int(result['year'])
            else:
                year = None
            result = TitleSearchResult(
                imdb_id=result['imdb_id'], title=result['title'],
                type=result['type'], year=year,
            )
            results.append(result)
        return tuple(results)

    def _get_writers(self, top_crew_data):
        return tuple(
            TitleName(
                name=i['name'],
                job=i.get('job'),
                category=i.get('category'),
                imdb_id=self._parse_id(i['id'])
            ) for i in top_crew_data['writers']
        )

    def _get_stars(self, principals_data):
        return tuple(
            TitleName(
                name=i['name'],
                job=i.get('job'),
                characters=tuple(i.get('characters', ())),
                category=i.get('category'),
                imdb_id=self._parse_id(i['id'])
            ) for i in principals_data
        )

    def _get_creators(self, top_crew_data):
        return tuple(
            TitleName(
                name=i['name'],
                job=i.get('job'),
                category=i.get('category'),
                imdb_id=self._parse_id(i['id'])
            ) for i in top_crew_data['writers']
            if i.get('job') == 'creator'
        )

    def _get_directors(self, top_crew_data):
        return tuple(
            TitleName(
                name=i['name'],
                job=i.get('job'),
                category=i.get('category'),
                imdb_id=self._parse_id(i['id'])
            ) for i in top_crew_data['directors']
        )

    def _get_credits(self, credits_data):
        credits = []
        for category in credits_data.get('credits', ()):
            for item in credits_data['credits'][category]:
                credits.append(TitleName(
                    name=item['name'],
                    category=item.get('category'),
                    job=item.get('job'),
                    imdb_id=self._parse_id(item['id'])
                ))
        return tuple(credits)

    def _parse_id(self, string):
        return REGEX_IMDB_ID.findall(string)[0]

    def _get_title_data(self, imdb_id):
        base_title_data = self._client.get_title(imdb_id=imdb_id)
        top_crew_data = self._client.get_title_top_crew(imdb_id=imdb_id)
        title_aux_data = self._client.get_title_auxiliary(imdb_id=imdb_id)
        credits_data = self._client.get_title_credits(imdb_id=imdb_id)

        title = base_title_data['base']['title']
        year = base_title_data['base'].get('year')
        try:
            rating = float(base_title_data['ratings']['rating'])
        except KeyError:
            rating = None
        type_ = base_title_data['base']['titleType'].lower()

        try:
            releases_data = self._client.get_title_releases(imdb_id=imdb_id)
        except LookupError:
            release_date = None
            releases = ()
        else:
            release_date = parse(releases_data['releases'][0]['date']).date()
            releases = tuple(
                TitleRelease(date=parse(r['date']).date(), region=r['region'])
                for r in releases_data['releases']
            )

        try:
            rating_count = base_title_data['ratings']['ratingCount']
        except KeyError:
            rating_count = 0

        try:
            plot_outline = base_title_data['plot']['outline']['text']
        except KeyError:
            plot_outline = None

        writers = self._get_writers(top_crew_data)
        directors = self._get_directors(top_crew_data)
        creators = self._get_creators(top_crew_data)
        try:
            genres = tuple(g.lower() for g in title_aux_data.get('genres'))
        except TypeError:
            genres = ()
        credits = self._get_credits(credits_data)

        try:
            certification = title_aux_data['certificate']['certificate']
        except TypeError:
            certification = None
        stars = self._get_stars(title_aux_data['principals'])
        try:
            image_data = title_aux_data['image']
            image = Image(
                url=image_data['url'],
                height=image_data['height'],
                width=image_data['width'],
            )
        except KeyError:
            image = None
        return dict(
            imdb_id=imdb_id,
            title=title,
            year=year,
            rating=rating,
            type=type_,
            release_date=release_date,
            releases=releases,
            plot_outline=plot_outline,
            rating_count=rating_count,
            writers=writers,
            directors=directors,
            creators=creators,
            genres=genres,
            credits=credits,
            certification=certification,
            image=image,
            stars=stars,
        ), title_aux_data
