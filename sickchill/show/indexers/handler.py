import re

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.tv import Show, TVEpisode

from .tvdb import TVDB


class ShowIndexer(object):
    TVDB = 1
    TVRAGE = 2
    FANART = 13
    TMDB = 14

    def __init__(self):
        if settings.INDEXER_DEFAULT is None:
            settings.INDEXER_DEFAULT = 1

        self.indexers = {1: TVDB()}
        self.__build_indexer_attribute_getters()

    def __getitem__(self, item):
        if isinstance(item, str):
            for index, indexer in self.indexers:
                if item in (indexer.name, indexer.slug):
                    return indexer

        if isinstance(item, tuple):
            item = item[0]

        return self.indexers[item]

    def __iter__(self):
        for i in self.indexers.items():
            yield i

    def __build_indexer_attribute_getters(self):
        indexers_attributes = ("name", "show_url", "slug", "languages", "lang_dict", "api_key", "base_url", "icon")

        def make_attribute_getter(_attribute):
            def indexer_attribute(indexer=None):
                # A value was passed, probably a string. Check keys and then try to convert it to int and check again
                if indexer is not None and not isinstance(indexer, int):
                    if indexer not in self.indexers:
                        if len(indexer) == 1:
                            check = try_int(indexer, indexer)
                            if check in self.indexers:
                                indexer = check

                    # Loop and find the right index
                    if indexer not in self.indexers:
                        for i in self.indexers:
                            # noinspection PyUnresolvedReferences
                            if indexer in (self.name(i), self.slug(i)):
                                indexer = i

                # If we didn't find it in our available indexers, use the default.
                if not indexer or indexer not in self.indexers:
                    indexer = settings.INDEXER_DEFAULT

                return getattr(self.indexers[indexer], _attribute)

            return indexer_attribute

        for attribute in indexers_attributes:
            setattr(self, attribute, make_attribute_getter(attribute))

    def search(self, indexer=None, *args, **kwargs):
        if indexer is None:
            indexer = settings.INDEXER_DEFAULT
        return self.indexers[indexer].search(*args, **kwargs)

    def search_indexers_for_series_name(self, name, language=None, exact=False):
        results = {}
        for i, indexer in self:
            search = indexer.search(name, language=language, exact=exact)
            if search:
                results[i] = search

        return results

    def search_indexers_for_series_id(self, name=None, indexerid=None, language=None, indexer=None):
        if not indexer:
            indexer = list(self.indexers)

        assert not isinstance(indexer, bytes)
        if isinstance(indexer, (int, str)):
            indexer = [indexer]

        assert not isinstance(name, bytes)

        if isinstance(name, str):
            name = [name]

        if indexerid:
            indexerid = int(indexerid)

        if not language:
            language = settings.INDEXER_DEFAULT_LANGUAGE

        assert bool(indexerid) or bool(name), "Must provide either a name or an indexer id to search indexers with"

        for n in name or "X":
            n = [re.sub("[. -]", " ", n)]
            for i in indexer:
                search = (name, indexerid)[bool(indexerid)]
                # noinspection PyUnresolvedReferences
                logger.debug("Trying to find {} on {}".format(search, self.name(i)))
                if indexerid:
                    result = self.indexers[i].get_series_by_id(indexerid, language)
                else:
                    result = self.indexers[i].get_series_by_name(n, indexerid, language)

                try:
                    # noinspection PyUnusedLocal
                    garbage = result.seriesName, result.id
                except AttributeError:
                    # noinspection PyUnresolvedReferences
                    logger.debug("Failed to find {} on {}".format(search, self.name(i)))
                    continue

                ShowObj = Show.find(settings.showList, result.id)
                if indexerid and ShowObj and ShowObj.indexerid == result.id:
                    return i, result
                elif indexerid and indexerid == result.id:
                    return i, result

        return None, None

    def series_by_id(self, indexerid, indexer, language):
        series = self.indexers[indexer].series(id=indexerid, language=language)
        if series:
            series.info(language)
        return series

    def series(self, show):
        result = self.series_by_id(indexerid=show.indexerid, indexer=show.indexer, language=show.lang)
        if result:
            result.info()
        return result

    def episodes(self, show, season):
        return self.indexers[show.indexer].episodes(show, season)

    def episode(self, item, season=None, episode=None, **kwargs):
        if isinstance(item, TVEpisode):
            show = item.show
            season = item.season
            episode = item.episode
        else:
            show = item

        return self.indexers[show.indexer].episode(show, season, episode, **kwargs)

    def series_poster_url_by_id(self, indexerid, language=None, indexer=None, thumb=False):
        class __TVShow(object):
            def __init__(self, __indexerid, __language, __indexer):
                self.indexerid = __indexerid
                self.indexer = __indexer or settings.INDEXER_DEFAULT
                self.lang = __language or settings.INDEXER_DEFAULT_LANGUAGE

        return self.series_poster_url(__TVShow(indexerid, language, indexer), thumb)

    def series_poster_url(self, show, thumb=False, multiple=False):
        return self.indexers[show.indexer].series_poster_url(show, thumb, multiple=multiple)

    def series_banner_url(self, show, thumb=False, multiple=False):
        return self.indexers[show.indexer].series_banner_url(show, thumb, multiple=multiple)

    def series_fanart_url(self, show, thumb=False, multiple=False):
        return self.indexers[show.indexer].series_fanart_url(show, thumb, multiple=multiple)

    def season_poster_url(self, show, season, thumb=False, multiple=False):
        return self.indexers[show.indexer].season_poster_url(show, season, thumb, multiple=multiple)

    def season_banner_url(self, show, season, thumb=False, multiple=False):
        return self.indexers[show.indexer].season_banner_url(show, season, thumb, multiple=multiple)

    def episode_image_url(self, episode):
        return self.indexers[episode.show.indexer].episode_image_url(episode)

    def get_indexer_favorites(self):
        results = []
        for indexer in self.indexers.values():
            results.extend(indexer.get_favorites())

        return results
