from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowFanArt(GenericMedia):
    def __init__(self, indexer_id, media_format):
        GenericMedia.__init__(self, indexer_id, media_format)

    def get_default_media_name(self):
        return 'fanart.png'

    def get_media_path(self):
        if self.get_show():
            return ImageCache().fanart_path(self.indexer_id)

        return ''
