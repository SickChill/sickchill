from sickchill import settings, logger
from sickchill.helper.common import try_int
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.sickbeard.classes import NZBSearchResult


class NZBProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.provider_type = GenericProvider.NZB
        self.torznab = False

    @property
    def is_active(self):
        return bool(settings.USE_NZBS) and self.is_enabled

    def _get_result(self, episodes):
        result = NZBSearchResult(episodes)
        if self.torznab or result.url.startswith('magnet'):
            result.resultType = GenericProvider.TORRENT

        return result

    def _get_size(self, item):
        try:
            size = item.get('links')[1].get('length', -1)
        except (AttributeError, IndexError, TypeError):
            size = -1

        if not size:
            logger.debug('The size was not found in the provider response')

        return try_int(size, -1)

    def _get_storage_dir(self):
        return settings.NZB_DIR
