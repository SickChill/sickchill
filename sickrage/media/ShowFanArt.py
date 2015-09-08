from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowFanArt(GenericMedia):
    """
    Get the fan art of a show
    """

    def get_default_media_name(self):
        return 'fanart.png'

    def get_media_path(self):
        if self.get_show():
            return ImageCache().fanart_path(self.indexer_id)

        return ''
