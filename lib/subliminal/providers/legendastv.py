# -*- coding: utf-8 -*-
import json
import logging
import os
import re

from babelfish import Language, language_converters
from datetime import datetime
from guessit import guess_file_info
from rarfile import RarFile, is_rarfile
from requests import Session
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, is_zipfile

from . import ParserBeautifulSoup, Provider
from ..cache import region, EPISODE_EXPIRATION_TIME, SHOW_EXPIRATION_TIME
from ..exceptions import AuthenticationError, ConfigurationError
from ..subtitle import Subtitle, fix_line_ending, guess_matches
from ..video import Episode, Movie, SUBTITLE_EXTENSIONS

TIMEOUT = 10

logger = logging.getLogger(__name__)
language_converters.register('legendastv = subliminal.converters.legendastv:LegendasTvConverter')


class LegendasTvSubtitle(Subtitle):
    provider_name = 'legendastv'

    def __init__(self, language, page_link, subtitle_id, name, imdb_id=None, guess=None, type=None, season=None,
                 year=None, no_downloads=None, rating=None, featured=False, multiple_episodes=False, timestamp=None):
        super(LegendasTvSubtitle, self).__init__(language, page_link=page_link)
        self.subtitle_id = subtitle_id
        self.name = name
        self.imdb_id = imdb_id
        self.type = type
        self.season = season
        self.year = year
        self.no_downloads = no_downloads
        self.rating = rating
        self.featured = featured
        self.multiple_episodes = multiple_episodes
        self.timestamp = timestamp
        self.guess = guess  # Do not need to guess it again if it was guessed before

    @property
    def id(self):
        return '%s (%s)' % (self.name, self.subtitle_id)

    def get_matches(self, video, hearing_impaired=False):
        matches = super(LegendasTvSubtitle, self).get_matches(video, hearing_impaired=hearing_impaired)

        # The best available information about a subtitle is its name. Using guessit to parse it.
        guess = self.guess if self.guess else guess_file_info(self.name + '.mkv', type=self.type)
        matches |= guess_matches(video, guess)

        # imdb_id match used only for movies
        if self.type == 'movie' and video.imdb_id and self.imdb_id == video.imdb_id:
            matches.add('imdb_id')

        return matches


class LegendasTvProvider(Provider):
    languages = {Language.fromlegendastv(l) for l in language_converters['legendastv'].codes}
    video_types = (Episode, Movie)
    server_url = 'http://legendas.tv'
    word_split_re = re.compile('(\w+)', re.IGNORECASE)

    def __init__(self, username=None, password=None):
        if username is not None and password is None or username is None and password is not None:
            raise ConfigurationError('Username and password must be specified')

        self.username = username
        self.password = password
        self.logged_in = False

    def initialize(self):
        self.session = Session()

        # login
        if self.username is not None and self.password is not None:
            logger.info('Logging in')
            data = {'_method': 'POST', 'data[User][username]': self.username, 'data[User][password]': self.password}
            r = self.session.post('%s/login' % self.server_url, data, allow_redirects=False, timeout=TIMEOUT)
            r.raise_for_status()

            soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
            auth_error = soup.find('div', {'class': 'alert-error'}, text=re.compile(u'.*Usuário ou senha inválidos.*'))

            if auth_error:
                raise AuthenticationError(self.username)

            logger.debug('Logged in')
            self.logged_in = True

    def terminate(self):
        # logout
        if self.logged_in:
            logger.info('Logging out')
            r = self.session.get('%s/users/logout' % self.server_url, timeout=TIMEOUT)
            r.raise_for_status()
            logger.debug('Logged out')
            self.logged_in = False

        self.session.close()

    def matches(self, expected, actual, ignore_episode=False):
        """
        Matches two dictionaries (expected and actual). The dictionary keys follow the guessit properties names.
        If the expected dictionary represents a movie:
          - ``type`` should match
          - ``title`` should match
          - ``year`` should match, unless they're not defined and expected and actual ``title``s are the same
        If the expected dictionary represents an episode:
          - ``type`` should match
          - ``series`` should match
          - ``eason`` should match
          - ``episodeNumber`` should match, unless ``ignore_episode`` is True

        :param expected: dictionary that contains the expected values
        :param actual: dictionary that contains the actual values
        :param ignore_episode: True if should ignore episodeNumber matching. Default: False
        :return: True if actual matches expected
        :rtype: bool
        """
        if expected.get('type') != actual.get('type'):
            return False

        if expected.get('type') == 'movie':
            if not self.name_matches(expected.get('title'), actual.get('title')):
                return False
            if expected.get('year') != actual.get('year'):
                if expected.get('year') and actual.get('year'):
                    return False
                if expected.get('title', '').lower() != actual.get('title', '').lower():
                    return False

        elif expected.get('type') == 'episode':
            if not self.name_matches(expected.get('series'), actual.get('series')):
                return False
            if expected.get('season') != actual.get('season'):
                return False
            if not ignore_episode and expected.get('episodeNumber') != actual.get('episodeNumber'):
                return False

        return True

    def name_matches(self, expected_name, actual_name):
        """
        Returns True if expected name and actual name matches. To be considered a match, actual_name should contain
        all words of expected_name in the order of appearance.

        :param expected_name:
        :param actual_name:
        :return: True if actual_name matches expected_name
        :rtype : bool
        """
        if not expected_name or not actual_name:
            return expected_name == actual_name

        words = self.word_split_re.findall(expected_name)
        name_regex_re = re.compile('(.*' + '\W+'.join(words) + '.*)', re.IGNORECASE)

        return name_regex_re.match(actual_name)

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def search_titles(self, params):
        """
        Returns shows or movies information by querying `/legenda/sugestao` page.
        Since the result is a list of suggestions (movies, tv shows, etc), additional filtering is required.
        Type (movies or series), name, year and/or season are used to filter out bad suggestions.

        :param params: dictionary containing the input parameters (title, series, season, episodeNumber, year)
        :return: shows or movies information
        :rtype: : ``list`` of ``dict``
        """

        keyword = params.get('title') if params.get('type') == 'movie' else params.get('series')
        logger.info('Searching titles using the keyword %s', keyword)
        r = self.session.get('%s/legenda/sugestao/%s' % (self.server_url, keyword), timeout=TIMEOUT)
        r.raise_for_status()

        # get the shows/movies out of the suggestions.
        # json sample:
        # [
        #    {
        #        "_index": "filmes",
        #        "_type": "filme",
        #        "_id": "24551",
        #        "_score": null,
        #        "_source": {
        #            "id_filme": "24551",
        #            "id_imdb": "903747",
        #            "tipo": "S",
        #            "int_genero": "1036",
        #            "dsc_imagen": "tt903747.jpg",
        #            "dsc_nome": "Breaking Bad",
        #            "dsc_sinopse": "Dos mesmos criadores de Arquivo X, mas n\u00e3o tem nada de sobrenatural nesta
        #                            s\u00e9rie. A express\u00e3o \"breaking bad\" \u00e9 usada quando uma coisa que
        #                            j\u00e1 estava ruim, fica ainda pior. E \u00e9 exatamente isso que acontece com
        #                            Walter White, um professor de qu\u00edmica, que vivia sua vida \"tranquilamente\"
        #                            quando, boom, um diagn\u00f3stico terminal muda tudo. O liberta. Ele come\u00e7a a
        #                            usar suas habilidades em qu\u00edmica de outra forma: montando um laborat\u00f3rio
        #                            de drogas para financiar o futuro de sua fam\u00edlia.",
        #            "dsc_data_lancamento": "2011",
        #            "dsc_url_imdb": "http:\/\/www.imdb.com\/title\/tt0903747\/",
        #            "dsc_nome_br": "Breaking Bad - 4\u00aa Temporada",
        #            "soundex": null,
        #            "temporada": "4",
        #            "id_usuario": "241436",
        #            "flg_liberado": "0",
        #            "dsc_data_liberacao": null,
        #            "dsc_data": "2011-06-12T21:06:42",
        #            "dsc_metaphone_us": "BRKNKBT0SSN",
        #            "dsc_metaphone_br": "BRKNKBTTMPRT",
        #            "episodios": null,
        #            "flg_seriado": null,
        #            "last_used": "1372569074",
        #            "deleted": false
        #        },
        #        "sort": [
        #            "4"
        #        ]
        #    }
        # ]
        #
        # Notes:
        #  tipo: Defines if the entry is a movie or a tv show (or a collection??)
        #  imdb_id: Sometimes it appears as a number and sometimes as a string prefixed with tt
        #  temporada: Sometimes is ``null`` and season information should be extracted from dsc_nome_br

        results = json.loads(r.text)

        # type, title, series, season, year follow guessit properties names
        mapping = dict(
            id='id_filme',
            type='tipo',
            title='dsc_nome',
            series='dsc_nome',
            season='temporada',
            year='dsc_data_lancamento',
            title_br='dsc_nome_br',
            imdb_id='id_imdb'
        )

        # movie and episode values follow guessit type values
        type_map = {
            'M': 'movie',
            'S': 'episode',
            'C': 'episode'  # Considering C as episode. Probably C stands for Collections
        }

        # Regex to extract the season number. e.g.: 3\u00aa Temporada, 1a Temporada, 2nd Season
        season_re = re.compile('.*? - (\d{1,2}).*?((emporada)|(Season))', re.IGNORECASE)

        # Regex to extract the IMDB id. e.g.: tt02342
        imdb_re = re.compile('t{0,2}(\d+)')

        candidates = []
        for result in results:
            entry = result['_source']
            item = {k: entry.get(v) for k, v in mapping.items()}
            item['type'] = type_map.get(item.get('type'), 'movie')
            item['imdb_id'] = (lambda m: m.group(1) if m else None)(imdb_re.search(item.get('imdb_id')))

            # Season information might be missing and it should be extracted from 'title_br'
            if not item.get('season') and item.get('title_br'):
                item['season'] = (lambda m: m.group(1) if m else None)(season_re.search(item.get('title_br')))

            # Some string fields are actually integers
            for field in ['season', 'year', 'imdb_id']:
                item[field] = (lambda v: int(v) if v and v.isdigit() else None)(item.get(field))

            # ignoring episode match since this first step is only about movie/season information
            if self.matches(params, item, ignore_episode=True):
                candidates.append(dict(item))

        logger.debug('Titles found: %s', candidates)
        return candidates

    def query(self, language, video, params):
        """
        Returns a list of subtitles based on the input parameters.
          - 1st step: initial lookup for the movie/show information (see ``search_titles``)
          - 2nd step: list all candidates all movies/shows from previous step
          - 3rd step: reject candidates that doesn't match the input parameters (wrong season, wrong episode, etc...)
          - 4th step: download all subtitles to inspect the 'release name',
           since each candidate might refer to several subtitles

        :param language: the requested language
        :param video: the input video
        :param params: the dictionary with the query parameters
        :return: a list of subtitles that matches the query parameters
        :rtype: ``list`` of ``LegendasTvSubtitle``
        """
        titles = self.search_titles(params)

        # The language code used by legendas.tv
        language_code = language.legendastv

        # Regex to extract rating information (number of downloads and rate). e.g.: 12345 downloads, nota 10
        rating_info_re = re.compile('(\d*) downloads, nota (\d{0,2})')

        # Regex to extract the last update timestamp. e.g.: 25/12/2014 - 19:25
        timestamp_info_re = re.compile('(\d{1,2}/\d{1,2}/\d{2,4} \- \d{1,2}:\d{1,2})')

        # Regex to identify the 'pack' suffix that candidates might have. e.g.: (p)Breaking.Bad.S05.HDTV.x264
        pack_name_re = re.compile('^\(p\)')

        # Regex to extract the subtitle_id from the 'href'. e.g.: /download/560014472eb4d/foo/bar
        subtitle_href_re = re.compile('/download/(\w+)/.+')

        subtitles = []
        # loop over matched movies/shows
        for title in titles:
            # page_url: {server_url}/util/carrega_legendas_busca_filme/{title_id}/{language_code}
            page_url = '%s/util/carrega_legendas_busca_filme/%s/%d' % (self.server_url, title.get('id'), language_code)

            # loop over paginated results
            while page_url:
                # query the server
                r = self.session.get(page_url, timeout=TIMEOUT)
                r.raise_for_status()

                soup = ParserBeautifulSoup(r.content, ['lxml', 'html.parser'])
                div_tags = soup.find_all('div', {'class': 'f_left'})

                # loop over each div which contains information about a single subtitle
                for div in div_tags:
                    link_tag = div.p.a

                    # Removing forward-slashes from the candidate name (common practice in legendas.tv), since it
                    # misleads guessit to identify the candidate name as a file in a specific folder (which is wrong).
                    candidate_name = pack_name_re.sub('', link_tag.string).replace('/', '.')
                    page_link = link_tag['href']
                    subtitle_id = (lambda m: m.group(1) if m else None)(subtitle_href_re.search(page_link))
                    multiple_episodes = bool(div.find_parent('div', {'class': 'pack'}) or
                                             pack_name_re.findall(link_tag.string))
                    featured = bool(div.find_parent('div', {'class': 'destaque'}))
                    no_downloads = (lambda v: int(v) if v and v.isdigit() else None)(
                        (lambda m: m.group(1) if m else None)(rating_info_re.search(div.text)))
                    rating = (lambda v: int(v) if v and v.isdigit() else None)(
                        (lambda m: m.group(2) if m else None)(rating_info_re.search(div.text)))
                    timestamp = (lambda d: datetime.strptime(d, '%d/%m/%Y - %H:%M') if d else None)(
                        (lambda m: m.group(1) if m else None)(timestamp_info_re.search(div.text)))

                    # Using the candidate name to filter out bad candidates
                    # (wrong type, wrong episode, wrong season or even wrong title)
                    guess = guess_file_info(candidate_name + '.mkv', type=title.get('type'))
                    if not self.matches(params, guess, ignore_episode=multiple_episodes):
                        continue

                    # Unfortunately, the only possible way to know the release names of a specific candidate is to
                    # download the compressed file (rar/zip) and list the file names.
                    subtitle_names = self.get_subtitle_names(subtitle_id, timestamp)

                    if not subtitle_names:
                        continue

                    for name in subtitle_names:
                        # Filtering out bad candidates (one archive might contain subtitles for the whole season,
                        # therefore this filtering is necessary) and some subtitles are in a relative folder inside the
                        # zip/rar file, therefore \ should be replaced by / in order to guess it properly
                        base_name = os.path.splitext(name)[0].replace('\\', '/')
                        guess = guess_file_info(base_name + '.mkv', type=title.get('type'))
                        if not self.matches(params, guess):
                            continue

                        subtitle = LegendasTvSubtitle(language, page_link, subtitle_id, name, guess=guess,
                                                      imdb_id=title.get('imdb_id'), type=title.get('type'),
                                                      season=title.get('season'), year=title.get('year'),
                                                      no_downloads=no_downloads, rating=rating, featured=featured,
                                                      multiple_episodes=multiple_episodes, timestamp=timestamp)

                        logger.debug('Found subtitle %s', subtitle)
                        subtitles.append(subtitle)

                next_page_link = soup.find('a', attrs={'class': 'load_more'}, text='carregar mais')
                page_url = self.server_url + next_page_link['href'] if next_page_link else None

        # High quality subtitles should have higher precedence when their scores are equal.
        subtitles.sort(key=lambda s: (s.featured, s.no_downloads, s.rating, s.multiple_episodes), reverse=True)

        return subtitles

    def list_subtitles(self, video, languages):
        """
        Returns a list of subtitles for the defined video and requested languages

        :param video:
        :param languages: the requested languages
        :return: a list of subtitles for the requested video and languages
        :rtype : ``list`` of ``LegendasTvSubtitles``
        """
        if isinstance(video, Episode):
            params = {'type': 'episode', 'series': video.series, 'season': video.season,
                      'episodeNumber': video.episode, 'year': video.year}
        elif isinstance(video, Movie):
            params = {'type': 'movie', 'title': video.title, 'year': video.year}

        return [s for l in languages for s in self.query(l, video, params) if params]

    def get_subtitle_names(self, subtitle_id, timestamp):
        """
        Returns all subtitle names for a specific subtitle_id. Only subtitle names are returned.

        :param subtitle_id: the id used to download the compressed file
        :param timestamp: represents the last update timestamp of the file
        :return: list of subtitle names
        :rtype: ``list`` of ``string``
        """
        return self._uncompress(
            subtitle_id, timestamp,
            lambda cf: [f for f in cf.namelist()
                        if 'legendas.tv' not in f.lower() and f.lower().endswith(SUBTITLE_EXTENSIONS)])

    def extract_subtitle(self, subtitle_id, subtitle_name, timestamp):
        """
        Extract the subtitle content from the compressed file. The file is downloaded, the subtitle_name is uncompressed
        and its contents is returned.

        :param subtitle_id: the id used to download the compressed file
        :param subtitle_name: the filename to be extracted
        :param timestamp: represents the last update timestamp of the file
        :return: the subtitle content
        :rtype : ``string``
        """
        return self._uncompress(subtitle_id, timestamp,
                                lambda cf, name: fix_line_ending(cf.read(name)), subtitle_name)

    def _uncompress(self, subtitle_id, timestamp, function, *args, **kwargs):
        content = self.download_content(subtitle_id, timestamp)

        # Download content might be a rar file (most common) or a zip.
        # Unfortunately, rarfile module only works with files (no in-memory streams)
        tmp = NamedTemporaryFile()
        try:
            tmp.write(content)
            tmp.flush()

            cf = RarFile(tmp.name) if is_rarfile(tmp.name) else (ZipFile(tmp.name) if is_zipfile(tmp.name) else None)

            return function(cf, *args, **kwargs) if cf else None
        finally:
            tmp.close()

    @region.cache_on_arguments(expiration_time=EPISODE_EXPIRATION_TIME)
    def download_content(self, subtitle_id, timestamp):
        """
        Downloads the compressed file for the specified subtitle_id. The timestamp is required in order to avoid the
        cache when the compressed file is updated (it's a common practice in legendas.tv to update the archive with new
        subtitles)

        :param subtitle_id: the id used to download the compressed file
        :param timestamp: represents the last update timestamp of the file
        :return: the downloaded file
        :rtype : ``bytes``
        """
        logger.debug('Downloading subtitle_id %s. Last update on %s' % (subtitle_id, timestamp))
        r = self.session.get('%s/downloadarquivo/%s' % (self.server_url, subtitle_id), timeout=TIMEOUT)
        r.raise_for_status()

        return r.content

    def download_subtitle(self, subtitle):
        subtitle.content = self.extract_subtitle(subtitle.subtitle_id, subtitle.name, subtitle.timestamp)
