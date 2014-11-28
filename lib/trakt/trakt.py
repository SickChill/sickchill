import hashlib
import requests

from . import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, apikey, username=None, password=None, use_https=False, timeout=5):
        self.apikey = apikey

        self.username = username
        self.password = password
        if password: hashlib.sha1(password.encode('utf-8')).hexdigest()

        self.protocol = 'https://' if use_https else 'http://'
        self.timeout = timeout

    def validateAccount(self):
        url = '/account/test/%APIKEY%'
        return self.traktRequest(url)

    def traktRequest(self, url, data=None):
        base_url = self.protocol + 'api.trakt.tv/%s' % url.replace('%APIKEY%', self.apikey).replace('%USER%',
                                                                                                    self.username)

        # request the URL from trakt and parse the result as json
        try:
            resp = requests.get(base_url,
                                auth=(self.username, self.password) if self.username and self.password else None,
                                data=data if data else [])

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except (requests.HTTPError, requests.ConnectionError) as e:
            if e.code == 401:
                raise traktAuthException(e.message, e.code)
            elif e.code == 503:
                raise traktServerBusy(e.message, e.code)
            else:
                raise traktException(e.message, e.code)

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp