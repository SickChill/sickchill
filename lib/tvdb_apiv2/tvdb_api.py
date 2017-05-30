# encoding:utf-8
# tvdb APIv2 for SickRage

import requests
import certifi
import json
import time
from sickbeard import logger

from tvdb_exceptions import (tvdb_exception)


class tvdbAPI:
    def __init__(self, apikey='0629B785CE550C8D', ssl_verify=True, timeout=30):
        self.session = requests.Session()
        self.verify = certifi.where() if ssl_verify else False
        self.timeout = timeout
        self.apikey = apikey
        self.token = None
        self.api_url = 'https://api-beta.thetvdb.com/'
        self.headers = {
            'Content-Type': 'application/json',
            'Accept-Language': 'en'
        }

    def _tvdb_token(self, refresh=False, count=0):
        if count > 3:
            return False
        elif count > 0:
            time.sleep(2)

        data = {
            'apikey': self.apikey
        }

        if refresh:
            data = None

        headers = None

        resp = self.tvdb_request('login', data=data, headers=headers, url=self.api_url, method='POST', count=count)

        if 'token' in resp:
            self.token = resp['token']

    def tvdb_request(self, path, data=None, headers=None, url=None, method='GET', count=0):
        if url is None:
            url = self.api_url

        count += 1

        if headers is None:
           headers = self.headers

        if self.token is not None:
            headers['Authorization'] = 'Bearer ' + self.token

        temp = json.dumps(data)

        try:
            resp = self.session.request(method, url + path, headers=headers, timeout=self.timeout,
                data=json.dumps(data) if data else [], verify=self.verify)

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                if 'timed out' in e:
                    logger.log(u'Timeout connecting to theTVDB. Try to increase timeout value in theTVDB settings', logger.WARNING)
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                else:
                    logger.log(u'Could not connect to theTVDB. Error: {0}'.format(e), logger.DEBUG)
            elif code == 502:
                logger.log(u'Retrying theTVDB api request: %s' % path, logger.DEBUG)
                return self.tvdb_request(path, data, headers, url, method)
            elif code == 401:
                if self.tvdb_token(refresh=True, count=count):
                    return self.tvdb_request(path, data, headers, url, method)
                else:
                    logger.log(u'Unauthorized. Please check your theTVDB settings', logger.WARNING)
            elif code in (500,501,503,504,520,521,522):
                # http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u'theTVDB may have some issues and it\'s unavailable. Try again later please', logger.DEBUG)
            elif code == 404:
                logger.log(u'theTVDB error (404) the resource does not exist: %s' % url + path, logger.ERROR)
            else:
                logger.log(u'Could not connect to theTVDB. Code error: {0}'.format(code), logger.ERROR)
            return {}

        # check and confirm tvdb call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise tvdb_exception(resp['message'])
            if 'error' in resp:
                raise tvdb_exception(resp['error'])
            else:
                raise tvdb_exception('Unknown Error')

        return resp

    def getidFromIMDB(self, imdbid):
        if not self.token:
            self._tvdb_token()

        resp = self.tvdb_request('search/series?imdbId=%s' % imdbid)
        return resp['data'][0]['id']

    def getidFromZap2It(self, zap2itid):
        if not self.token:
            self._tvdb_token()

        resp = self.tvdb_request('search/series?imdbId=%s' % zap2itId)
        return resp['data'][0]['id']

    def getUpdates(self, start='1449192688'):
        if not self.token:
            self._tvdb_token()

        resp = self.tvdb_request('updated/query?fromTime=%s' % start)
        return resp
