import requests
import json
from sickbeard import logger

from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, apikey, username=None, password=None, timeout=5):
        self.username = username
        self.password = password
        self.timeout = timeout
        self.api_url = 'https://api.trakt.tv/'
        self.headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': apikey,
        }

    def validateAccount(self):
        if hasattr(self, 'token'):
            del(self.token)
        data = {
            'login': self.username,
            'password': self.password
        }
        try:
            resp = requests.request('POST', self.api_url+"auth/login",
                headers=self.headers, data=json.dumps(data))
            resp.raise_for_status()
            resp = resp.json()
        except (requests.HTTPError, requests.ConnectionError) as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise traktException(e)
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u"Retrying trakt api request: auth/login", logger.WARNING)
                return self.validateAccount()
            elif code == 401:
                raise traktAuthException(e)
            elif code == 503:
                raise traktServerBusy(e)
            else:
                raise traktException(e)
        if 'token' in resp:
            self.token = resp['token']
            return True
        return False

    def traktRequest(self, path, data=None, method='GET'):
        url = self.api_url + path
        headers = self.headers
        if not getattr(self, 'token', None):
            self.validateAccount()
        headers['trakt-user-login'] = self.username
        headers['trakt-user-token'] = self.token

        # request the URL from trakt and parse the result as json
        try:
            resp = requests.request(method, url, headers=headers, data=json.dumps(data) if data else [])

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except (requests.HTTPError, requests.ConnectionError) as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise traktException(e)
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u"Retrying trakt api request: %s" % path, logger.WARNING)
                return self.traktRequest(path, data, method)
            elif code == 401:
                raise traktAuthException(e)
            elif code == 503:
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