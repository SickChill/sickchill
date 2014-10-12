# -*- coding: utf-8 -*-
# Copyright 2012 Ofir Brukner <ofirbrukner@gmail.com>
#
# This file is part of subliminal.
#
# subliminal is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# subliminal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with subliminal.  If not, see <http://www.gnu.org/licenses/>.
import logging
import re
import json
import os
from . import ServiceBase
from ..exceptions import DownloadFailedError, ServiceError
from ..language import language_set
from ..subtitles import get_subtitle_path, ResultSubtitle
from ..videos import Episode, Movie
from ..utils import to_unicode, get_keywords


logger = logging.getLogger("subliminal")


class Subscenter(ServiceBase):
    server_url = 'http://subscenter.cinemast.com/he/'
    site_url = 'http://subscenter.cinemast.com/'
    api_based = False
    languages = language_set(['he', 'en'])
    videos = [Episode, Movie]
    require_video = False
    required_features = ['permissive']

    @staticmethod
    def slugify(string):
        new_string = string.replace(' ', '-').replace("'", '').replace(':', '').lower()
        # We remove multiple spaces by using this regular expression.
        return re.sub('-+', '-', new_string)

    def list_checked(self, video, languages):
        series = None
        season = None
        episode = None
        title = video.title
        if isinstance(video, Episode):
            series = video.series
            season = video.season
            episode = video.episode
        return self.query(video.path or video.release, languages, get_keywords(video.guess), series, season,
                          episode, title)

    def query(self, filepath, languages=None, keywords=None, series=None, season=None, episode=None, title=None):
        logger.debug(u'Getting subtitles for %s season %d episode %d with languages %r' % (series, season, episode, languages))
        # Converts the title to Subscenter format by replacing whitespaces and removing specific chars.
        if series and season and episode:
            # Search for a TV show.
            kind = 'episode'
            slugified_series = self.slugify(series)
            url = self.server_url + 'cinemast/data/series/sb/' + slugified_series + '/' + str(season) + '/' + \
                   str(episode) + '/'
        elif title:
            # Search for a movie.
            kind = 'movie'
            slugified_title = self.slugify(title)
            url = self.server_url + 'cinemast/data/movie/sb/' + slugified_title + '/'
        else:
            raise ServiceError('One or more parameters are missing')
        logger.debug('Searching subtitles %r', {'title': title, 'season': season, 'episode': episode})
        response = self.session.get(url)
        if response.status_code != 200:
            raise ServiceError('Request failed with status code %d' % response.status_code)

        subtitles = []
        response_json = json.loads(response.content)
        for lang, lang_json in response_json.items():
            lang_obj = self.get_language(lang)
            if lang_obj in self.languages and lang in languages:
                for group_data in lang_json.values():
                    for quality in group_data.values():
                        for sub in quality.values():
                            release = sub.get('subtitle_version')
                            sub_path = get_subtitle_path(filepath, lang_obj, self.config.multi)
                            link = self.server_url + 'subtitle/download/' + lang + '/' + str(sub.get('id')) + \
                                            '/?v=' + release + '&key=' + str(sub.get('key'))
                            subtitles.append(ResultSubtitle(sub_path, lang_obj, self.__class__.__name__.lower(),
                                                            link, release=to_unicode(release)))
        return subtitles

    def download(self, subtitle):
        logger.info(u'Downloading %s in %s' % (subtitle.link, subtitle.path))
        try:
            r = self.session.get(subtitle.link, headers={'Referer': subtitle.link, 'User-Agent': self.user_agent})
            if r.status_code != 200:
                raise DownloadFailedError('Request failed with status code %d' % r.status_code)
            if r.headers['Content-Type'] == 'text/html':
                raise DownloadFailedError('Download limit exceeded')
            with open(subtitle.path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logger.error(u'Download failed: %s' % e)
            if os.path.exists(subtitle.path):
                os.remove(subtitle.path)
            raise DownloadFailedError(str(e))
        logger.debug(u'Download finished')
        return subtitle


Service = Subscenter