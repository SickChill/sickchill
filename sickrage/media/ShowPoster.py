from sickbeard.image_cache import ImageCache
from sickrage.media.GenericMedia import GenericMedia


class ShowPoster(GenericMedia):
    def __init__(self, indexer_id, media_format):
        GenericMedia.__init__(self, indexer_id, media_format)

    def get_default_media_name(self):
        return 'poster.png'

    def get_media_path(self):
        if self.get_show():
            if self.media_format is 'normal':
                return ImageCache().poster_path(self.indexer_id)

            if self.media_format is 'thumb':
                return ImageCache().poster_thumb_path(self.indexer_id)

        return ''
