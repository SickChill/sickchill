import json
import re

import sickchill
from sickchill import settings
from sickchill.oldbeard.helpers import make_indexer_session
from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.show.indexers.handler import ShowIndexer
from sickchill.show.Show import Show
from sickchill.views.home import Home
from sickchill.views.routes import Route


@Route("/imageSelector(/?.*)", name="imageselector")
class ImageSelector(Home):
    def initialize(self):
        super().initialize()
        self.indexer_session = make_indexer_session()

    def index(self, show=None, imageType="", provider: int | None = None):
        if not show:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        show_obj = Show.find(settings.show_list, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        # Handle Upload option (-1)
        if provider == -1 or provider is None or str(provider) == "-1":
            # For upload, we don't return external images — just an empty list
            # The frontend handles the upload locally
            return json.dumps([])

        try:
            provider = int(provider)
        except (TypeError, ValueError):
            provider = None

        if provider == ShowIndexer.FANART:
            metadata_generator = GenericMetadata()
            images = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, imageType, multiple=True)
            images = list({"image": image, "thumb": re.sub("/fanart/", "/preview/", image)} for image in images)
        elif provider == ShowIndexer.TMDB:
            metadata_generator = GenericMetadata()
            images = metadata_generator._retrieve_show_image_urls_from_tmdb(show_obj, imageType, multiple=True)
            images = list({"image": image, "thumb": image} for image in images)
        else:
            if "poster" == imageType:
                images = sickchill.indexer[provider].series_poster_url(show_obj, multiple=True)
            elif "banner" == imageType:
                images = sickchill.indexer[provider].series_banner_url(show_obj, multiple=True)
            elif "fanart" == imageType:
                images = sickchill.indexer[provider].series_fanart_url(show_obj, multiple=True)
            else:
                return self._genericMessage(_("Error"), _("Invalid image provider"))

            images = list({"image": image, "thumb": image} for image in images)

        return json.dumps(images)

    def url_wrap(self):
        """
        Wrap Image URL so it has our host and does not trigger ADBlock.
        @return: redirect
        """
        from sickchill.providers.metadata.helpers import is_allowed_show_image_url

        url = self.get_query_argument("url")
        if not is_allowed_show_image_url(url):
            return self.write_error(404)

        request = self.indexer_session.get(url, stream=True)
        return request.content
