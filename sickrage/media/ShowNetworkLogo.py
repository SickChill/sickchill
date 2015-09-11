from os.path import join
from sickbeard.encodingKludge import ek
from sickrage.media.GenericMedia import GenericMedia


class ShowNetworkLogo(GenericMedia):
    """
    Get the network logo of a show
    """

    def get_default_media_name(self):
        return join('network', 'nonetwork.png')

    def get_media_path(self):
        show = self.get_show()

        if show:
            return ek(join, self.get_media_root(), 'images', 'network', show.network_logo_name + '.png')

        return ''
