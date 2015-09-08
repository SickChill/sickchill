from sickrage.media.GenericMedia import GenericMedia


class ShowNetworkLogo(GenericMedia):
    """
    Get the network logo of a show
    """

    def get_default_media_name(self):
        return 'network/nonetwork.png'

    def get_media_path(self):
        show = self.get_show()

        if show:
            return '%s/images/network/%s.png' % (self.get_media_root(), show.network_logo_name)

        return ''
