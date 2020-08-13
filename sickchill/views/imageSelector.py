import json
import re

import sickchill
from sickchill import settings
from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.show.Show import Show

from .index import WebRoot
from .routes import Route


@Route('/imageSelector(/?.*)', name='imageselector')
class ImageSelector(WebRoot):
    def __init__(self, *args, **kwargs):
        super(ImageSelector, self).__init__(*args, **kwargs)

    def index(self, show=None, image_type='', provider=None):
        if not show:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        show_obj = Show.find(settings.showList, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header('Content-Type', 'application/json')
        metadata_generator = GenericMetadata()

        if provider == 'fanart':
            images = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, image_type, multiple=True)
            images = list(map(lambda image: {'image': image, 'thumb': re.sub('/fanart/', '/preview/', image)}, images))
        else:
            images = sickchill.indexer.series_poster_url(show_obj, multiple=True)
            # image_url = sickchill.indexer.series_poster_url_by_id(indexerId)

        return json.dumps(images)
