"""
Created by Nyaran, based on https://github.com/realgam3/service.subtitles.bsplayer
"""
import logging
import os
import random
import re
import struct
import zlib
from time import sleep
from xml.etree import ElementTree
from xmlrpc.client import ServerProxy

from babelfish import Language, language_converters
from requests import Session
from subliminal import __short_version__
from subliminal.providers import Provider, TimeoutSafeTransport
from subliminal.subtitle import fix_line_ending, Subtitle

from sickchill import settings
from sickchill.oldbeard.helpers import make_context

logger = logging.getLogger(__name__)

# s1-9, s101-109
SUB_DOMAINS = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s101", "s102", "s103", "s104", "s105", "s106", "s107", "s108", "s109"]
API_URL_TEMPLATE = "http://{sub_domain}.api.bsplayer-subtitles.com/v1.php"


def get_sub_domain():
    sub_domains_end = len(SUB_DOMAINS) - 1
    return API_URL_TEMPLATE.format(sub_domain=SUB_DOMAINS[random.randint(0, sub_domains_end)])


class BSPlayerSubtitle(Subtitle):
    """BSPlayer Subtitle."""

    provider_name = "bsplayer"
    series_re = re.compile(r'^"(?P<series_name>.*)" (?P<series_title>.*)$')

    def __init__(
        self,
        subtitle_id,
        size,
        page_link,
        language,
        filename,
        subtitle_source,
        subtitle_hash,
        rating,
        season,
        episode,
        encoding,
        imdb_id,
        imdb_rating,
        movie_year,
        movie_name,
        movie_hash,
        movie_size,
        movie_fps,
    ):
        super().__init__(language, page_link=page_link, encoding=encoding)
        self.subtitle_id = subtitle_id
        self.size = size
        self.page_link = page_link
        self.language = language
        self.filename = filename
        self.source = subtitle_source
        self.hash = subtitle_hash
        self.rating = rating
        self.season = season
        self.episode = episode
        self.encoding = encoding
        self.imdb_id = imdb_id
        self.imdb_rating = imdb_rating
        self.movie_year = movie_year
        self.movie_name = movie_name
        self.movie_hash = movie_hash
        self.movie_size = movie_size
        self.movie_fps = movie_fps

    @property
    def id(self):
        return str(self.subtitle_id)

    @property
    def info(self):
        if not self.filename and not self.movie_name:
            return self.subtitle_id
        if self.movie_name and len(self.movie_name) > len(self.filename):
            return self.movie_name
        return self.filename

    @property
    def series_name(self):
        return self.series_re.match(self.movie_name).group("series_name")

    @property
    def series_title(self):
        return self.series_re.match(self.movie_name).group("series_title")

    def get_matches(self, video):
        return {"hash"}


class BSPlayerProvider(Provider):
    """BSPlayer Provider."""

    languages = {Language.fromalpha3b(l) for l in language_converters["alpha3b"].codes}
    server_url = "https://api.bsplayer.org/xml-rpc"
    user_agent = "subliminal v%s" % __short_version__

    def __init__(self, search_url=None):
        self.server = ServerProxy(self.server_url, TimeoutSafeTransport(10), context=make_context(settings.SSL_VERIFY))
        # None values not allowed for logging in, so replace it by ''
        self.token = None
        self.session = Session()
        self.search_url = search_url or get_sub_domain()

    def _api_request(self, func_name="logIn", params="", tries=5):
        headers = {
            "User-Agent": "BSPlayer/2.x (1022.12360)",
            "Content-Type": "text/xml; charset=utf-8",
            "Connection": "close",
            "SOAPAction": '"http://api.bsplayer-subtitles.com/v1.php#{func_name}"'.format(func_name=func_name),
        }
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ns1="{self.search_url}">'
            '<SOAP-ENV:Body SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            f"<ns1:{func_name}>{params}</ns1:{func_name}></SOAP-ENV:Body></SOAP-ENV:Envelope>"
        )

        for i in range(tries):
            try:
                res = self.session.post(self.search_url, data=data, headers=headers)
                return ElementTree.fromstring(res.content)
            except ElementTree.ParseError:
                logger.warning(f"[BSPlayer]: {res.content}")
            except Exception as ex:
                logger.error("[BSPlayer] ERROR: %s." % ex)
                if func_name == "logIn":
                    self.search_url = get_sub_domain()
                sleep(2)
        logger.error("[BSPlayer] ERROR: Too many tries (%d)..." % tries)

    def initialize(self):
        root = self._api_request(func_name="logIn", params=("<username></username>" "<password></password>" "<AppID>BSPlayer v2.67</AppID>"))
        res = root.find(".//return")
        if res.find("status").text == "OK":
            self.token = res.find("data").text

    def terminate(self):
        root = self._api_request(func_name="logOut", params=f"<handle>{self.token}</handle>")
        res = root.find(".//return")
        if res.find("status").text != "OK":
            logger.error("[BSPlayer] ERROR: Unable to close session.")
        self.token = None

    def query(self, languages, name_hash=None, size=None):
        # fill the search criteria
        root = self._api_request(
            func_name="searchSubtitles",
            params=(
                "<handle>{token}</handle>"
                "<movieHash>{movie_hash}</movieHash>"
                "<movieSize>{movie_size}</movieSize>"
                "<languageId>{language_ids}</languageId>"
                "<imdbId>*</imdbId>"
            ).format(token=self.token, movie_hash=name_hash, movie_size=size, language_ids=",".join([l.alpha3 for l in languages])),
        )
        res = root.find(".//return/result")
        if res.find("status").text != "OK":
            return []

        items = root.findall(".//return/data/item")
        subtitles = []
        if items:
            for item in items:
                subtitle_id = item.find("subID").text
                size = item.find("subSize").text
                download_link = item.find("subDownloadLink").text
                language = Language.fromalpha3b(item.find("subLang").text)
                filename = item.find("subName").text
                subtitle_source = item.find("subFormat").text
                subtitle_hash = item.find("subHash").text
                rating = item.find("subRating").text
                season = item.find("season").text
                episode = item.find("episode").text
                encoding = item.find("encsubtitle").text
                imdb_id = item.find("movieIMBDID").text
                imdb_rating = item.find("movieIMBDRating").text
                movie_year = item.find("movieYear").text
                movie_name = item.find("movieName").text
                movie_hash = item.find("movieHash").text
                movie_size = item.find("movieSize").text
                movie_fps = item.find("movieFPS").text

                subtitle = BSPlayerSubtitle(
                    subtitle_id,
                    size,
                    download_link,
                    language,
                    filename,
                    subtitle_source,
                    subtitle_hash,
                    rating,
                    season,
                    episode,
                    encoding,
                    imdb_id,
                    imdb_rating,
                    movie_year,
                    movie_name,
                    movie_hash,
                    movie_size,
                    movie_fps,
                )
                logger.debug("Found subtitle %s", subtitle)

                subtitles.append(subtitle)

        return subtitles

    def list_subtitles(self, video, languages):
        return self.query(languages, name_hash=self.hash_bsplayer(video.name), size=video.size)

    def download_subtitle(self, subtitle):
        logger.info("Downloading subtitle %r", subtitle)
        headers = {
            "User-Agent": "BSPlayer/2.x (1022.12360)",
            "Content-Length": "0",
        }

        response = self.session.get(subtitle.page_link, headers=headers)

        subtitle.content = fix_line_ending(zlib.decompress(response.content, 47))

    @staticmethod
    def hash_bsplayer(video_path):
        """Compute a hash using BSPlayer's algorithm.
        :param str video_path: path of the video.
        :return: the name_hash.
        :rtype: str
        """
        little_endian_long_long = "<q"  # little-endian long long
        byte_size = struct.calcsize(little_endian_long_long)

        with open(video_path, "rb") as f:
            file_size = os.path.getsize(video_path)
            file_hash = file_size

            if file_size < 65536 * 2:
                return

            for _ in range(65536 // byte_size):
                buff = f.read(byte_size)
                (l_value,) = struct.unpack(little_endian_long_long, buff)
                file_hash += l_value
                file_hash &= 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

            f.seek(max(0, file_size - 65536), 0)

            for x in range(65536 // byte_size):
                buff = f.read(byte_size)
                (l_value,) = struct.unpack(little_endian_long_long, buff)
                file_hash += l_value
                file_hash &= 0xFFFFFFFFFFFFFFFF

        return "%016x" % file_hash
