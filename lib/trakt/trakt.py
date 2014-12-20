import requests

from requests.auth import HTTPBasicAuth
from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, apikey, username=None, password=None, use_https=False, timeout=5):
        self.apikey = apikey
        self.username = username
        self.password = password

        self.protocol = 'https://' if use_https else 'http://'
        self.timeout = timeout

    def validateAccount(self):
        return self.traktRequest("account/test/%APIKEY%", method='POST')

    def traktRequest(self, url, data=None, method='GET'):
        base_url = self.protocol + 'api.trakt.tv/%s' % url.replace('%APIKEY%', self.apikey).replace('%USER%',
                                                                                                    self.username)

        # request the URL from trakt and parse the result as json
        try:
            resp = requests.request(method, base_url, auth=HTTPBasicAuth(self.username, self.password), data=data if data else [])

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except (requests.HTTPError, requests.ConnectionError) as e:
            if e.response.status_code == 401:
                raise traktAuthException(e)
            elif e.response.status_code == 503:
                raise traktServerBusy(e)
            else:
                raise traktException(e)

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp