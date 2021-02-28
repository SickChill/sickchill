import re
from pathlib import Path

from sqlalchemy import Integer, Unicode
from sqlalchemy.types import TypeDecorator


class RegexType(TypeDecorator):
    impl = Unicode
    python_type = re.Pattern

    def process_bind_param(self, value, dialect):
        if isinstance(value, re.Pattern):
            return value.pattern
        return value

    def process_result_value(self, value, dialect):
        return re.compile(value, re.IGNORECASE | re.UNICODE)


class PathType(TypeDecorator):
    impl = Unicode
    python_type = Path

    def process_bind_param(self, value, dialect):
        if isinstance(value, Path):
            value = value.resolve()
            assert value.exists()

        return value

    def process_result_value(self, value, dialect):
        return Path(value).resolve()


class ChoiceType(TypeDecorator):

    impl = Integer

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        for key, val in self.choices.items():
            if value in (key, val):
                return val

    def process_result_value(self, value, dialect):
        return self.choices[value]


IGNORED = _('Ignored')
PREFERRED = _('Preferred')
REQUIRED = _('Required')
ALLOWED = _('Allowed')
DesireTypes = {IGNORED: 0, REQUIRED: 1, PREFERRED: 2, ALLOWED: 3}

SEARCHED = _('Searched')
SNATCHED = _('Release Snatched')
DOWNLOADED = _('Release Downloaded')
PROCESSED = _('Release Processed')
FAILED = _('Release Failed')
SUBTITLED = _('Subtitles Downloaded')
HistoryActions = {SEARCHED: 0, SNATCHED: 1, DOWNLOADED: 2, PROCESSED: 3, FAILED: 4, SUBTITLED: 5}

BANNER = _('Banner')
POSTER = _('Poster')
COVER = _('Cover Art')
DISC_ART = _('Disc Art')
ImageTypes = {BANNER: 0, POSTER: 1, COVER: 2, DISC_ART: 3}

TVDB = _('theTVDB')
TMDB = _('TMDB')
OMDB = _('oMDB')
IMDB = _('IMDb')
MAZE = _('TvMAZE')
IndexerNames = {TVDB: 0, TMDB: 1, OMDB: 2, IMDB: 3, MAZE: 4}

SERIES = _('Show')
SEASON = _('Season')
EPISODE = _('Episode')
MOVIE = _('Movie')
ReleaseTypeNames = {SERIES: 0, SEASON: 1, EPISODE: 2, MOVIE: 3}
