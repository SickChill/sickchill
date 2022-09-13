class Notifier(object):
    def notify_snatch(self, ep_name):
        raise NotImplementedError

    def notify_download(self, ep_name):
        raise NotImplementedError

    def notify_subtitle_download(self, ep_name, lang):
        raise NotImplementedError

    def notify_update(self, new_version):
        raise NotImplementedError

    def notify_login(self, ipaddress=""):
        raise NotImplementedError

    @staticmethod
    def test_notify(username):
        raise NotImplementedError
