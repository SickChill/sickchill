import abc

from sickchill import settings


class Indexer(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        self.name = "Generic"
        self.slug = "generic"

        self.language = settings.INDEXER_DEFAULT_LANGUAGE
        self.indexer = settings.INDEXER_DEFAULT
        self.timeout = settings.INDEXER_TIMEOUT

    @abc.abstractmethod
    def search(self, name, language=None, exact=False, indexer_id=False):
        raise NotImplementedError

    @abc.abstractmethod
    def get_series_by_id(self, indexerid, language=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_series_by_name(self, indexerid, language=None):
        raise NotImplementedError

    @abc.abstractmethod
    def episodes(self, show, season):
        raise NotImplementedError

    @abc.abstractmethod
    def episode(self, show, season, episode):
        raise NotImplementedError

    @property
    def languages(self):
        raise NotImplementedError

    @property
    def lang_dict(self):
        raise NotImplementedError
