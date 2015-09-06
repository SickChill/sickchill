from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowBanner(GenericMedia):
    """
    Get the banner of a show
    """

    def get_default_media_name(self):
        return 'banner.png'

    def get_media_path(self):
        if self.get_show():
            if self.media_format == 'normal':
                return ImageCache().banner_path(self.indexer_id)

            if self.media_format == 'thumb':
                return ImageCache().banner_thumb_path(self.indexer_id)

        return ''
