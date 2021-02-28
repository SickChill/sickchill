import re
from pathlib import Path

from sqlalchemy import Unicode
from sqlalchemy.types import TypeDecorator

from .utils import make_labeled_enum


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


DesireTypes = make_labeled_enum(
    'DesireTypes',
    {
        'IGNORED': _('Ignored'),
        'PREFERRED': _('Preferred'),
        'REQUIRED': _('Required'),
        'ALLOWED': _('Allowed')
    }
)

HistoryActions = make_labeled_enum(
    'HistoryActions',
    {
        'SEARCHED': _('Searched'),
        'SNATCHED': _('Release Snatched'),
        'DOWNLOADED': _('Release Downloaded'),
        'PROCESSED': _('Release Processed'),
        'FAILED': _('Release Failed'),
        'SUBTITLED': _('Subtitles Downloaded')
    }
)

ImageTypes = make_labeled_enum(
    'ImageTypes',
    {
        'BANNER': _('Banner'),
        'POSTER': _('Poster'),
        'COVER': _('Cover Art'),
        'DISC_ART': _('Disc Art')
    }
)

IndexerNames = make_labeled_enum(
    'IndexerNames',
    {
        'TVDB': _('theTVDB'),
        'TMDB': _('TMDB'),
        'OMDB': _('oMDB'),
        'IMDB': _('IMDb'),
        'MAZE': _('TvMAZE')
    }
)

ReleaseTypeNames = make_labeled_enum(
    'ReleaseTypeNames',
    {
        'SERIES': _('Show'),
        'SEASON': _('Season'),
        'EPISODE': _('Episode'),
        'MOVIE': _('Movie')
    }
)
