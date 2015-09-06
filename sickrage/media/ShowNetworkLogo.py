import sickbeard

from sickrage.media.GenericMedia import GenericMedia


class ShowNetworkLogo(GenericMedia):
    def __init__(self, indexer_id, media_format):
        GenericMedia.__init__(self, indexer_id, media_format)

    def get_default_media_name(self):
        return 'network/nonetwork.png'

    def get_media_path(self):
        show = self.get_show()

        if show:
            return '%s/images/network/%s.png' % (self.get_media_root(), show.network_logo_name)

        return ''

    def get_media_root(self):
        return sickbeard.DATA_DIR + '/gui/slick'
