
# Stdlib Imports

# Stdlib Imports
from urllib.parse import urljoin

# Third Party Imports
from requests.auth import HTTPDigestAuth

# First Party Imports
from sickchill import settings
from sickchill.sickbeard.clients.generic import GenericClient


class Client(GenericClient):

    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('qBittorrent', host, username, password)
        self.url = self.host
        self.api_prefix = 'api/v2/'
        self.session.auth = HTTPDigestAuth(self.username, self.password)
        self.session.headers.update({
            'Origin': self.host,
            'Referer': self.host
        })

    @property
    def api(self):
        try:
            self.url = urljoin(self.host, self.api_prefix + 'app/webapiVersion')
            response = self.session.get(self.url, verify=settings.TORRENT_VERIFY_CERT)
            if response.status_code == 401:
                version = None
            else:
                version = float(response.content)
        except Exception:
            version = 2
        return version

    def _get_auth(self):
        if self.api is None:
            return None
        self.url = urljoin(self.host, self.api_prefix + 'auth/login')
        data = {'username': self.username, 'password': self.password}
        try:
            self.response = self.session.post(self.url, data=data)
        except Exception:
            return None
        self.session.cookies = self.response.cookies
        self.auth = self.response.content
        return (None, self.auth)[self.response.status_code != 403]

    def _add_torrent_uri(self, result):
        data = {'urls': result.url}
        self.url = urljoin(self.host, self.api_prefix + 'torrents/add')
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_file(self, result):
        files = {'torrents': (result.name + '.torrent', result.content)}
        self.url = urljoin(self.host, self.api_prefix + 'torrents/add')
        return self._request(method='post', files=files, cookies=self.session.cookies)

    def _set_torrent_label(self, result):
        label = settings.TORRENT_LABEL
        if result.show.is_anime:
            label = settings.TORRENT_LABEL_ANIME
        self.url = urljoin(self.host, self.api_prefix + 'torrents/setCategory')
        data = {'hashes': result.hash.lower(), 'category': label.replace(' ', '_')}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_priority(self, result):
        self.url = urljoin(self.host, self.api_prefix + 'app/preferences')
        self._request(method='get', cookies=self.session.cookies)
        json = self.response.json()
        if json and json.get('queueing_enabled'):
            self.url = urljoin(self.host, self.api_prefix + 'torrents/decreasePrio?hashes={}'.format(result.hash.lower))
            if result.priority == 1:
                self.url = urljoin(self.host, self.api_prefix + 'torrents/increasePrio?hashes={}'.format(result.hash.lower))
            return self._request(method='get', cookies=self.session.cookies)

    def _set_torrent_pause(self, result):
        self.url = urljoin(self.host, self.api_prefix + 'torrents/resume?hashes={}'.format(result.hash.lower()))
        if settings.TORRENT_PAUSED:
            self.url = urljoin(self.host, self.api_prefix + 'torrents/pause?hashes={}'.format(result.hash.lower()))
        return self._request(method='get', cookies=self.session.cookies)
