from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowPoster(GenericMedia):
    """
    Get the poster of a show
    """

    def get_default_media_name(self):
        return 'poster.png'

    def get_media_path(self):
        if self.get_show():
            if self.media_format == 'normal':
                return ImageCache().poster_path(self.indexer_id)

            if self.media_format == 'thumb':
                return ImageCache().poster_thumb_path(self.indexer_id)

        return ''
