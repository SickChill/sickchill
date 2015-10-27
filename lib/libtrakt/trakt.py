import requests
import certifi
import json
import sickbeard
import time
from sickbeard import logger

from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, ssl_verify=True, timeout=30):
        self.session = requests.Session()
        self.verify = certifi.where() if ssl_verify else False
        self.timeout = timeout if timeout else None
        self.auth_url = sickbeard.TRAKT_OAUTH_URL
        self.api_url = sickbeard.TRAKT_API_URL
        self.headers = {
          'Content-Type': 'application/json',
          'trakt-api-version': '2',
          'trakt-api-key': sickbeard.TRAKT_API_KEY
        }

    def traktToken(self, trakt_pin=None, refresh=False, count=0):
   
        if count > 3:
            sickbeard.TRAKT_ACCESS_TOKEN = ''
            return False
        elif count > 0:
            time.sleep(2)



        data = {
            'client_id': sickbeard.TRAKT_API_KEY,
            'client_secret': sickbeard.TRAKT_API_SECRET,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
        }

        if refresh:
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = sickbeard.TRAKT_REFRESH_TOKEN
        else:
            data['grant_type'] = 'authorization_code'
            if not None == trakt_pin:
                data['code'] = trakt_pin
       
        headers = {
            'Content-Type': 'application/json'
        }

        resp = self.traktRequest('oauth/token', data=data,  headers=headers, url=self.auth_url , method='POST', count=count)

        if 'access_token' in resp:
            sickbeard.TRAKT_ACCESS_TOKEN  = resp['access_token']
            if 'refresh_token' in resp:
                sickbeard.TRAKT_REFRESH_TOKEN = resp['refresh_token']
            return True
        return False
       
    def validateAccount(self):
           
        resp = self.traktRequest('users/settings')
       
        if 'account' in resp:
            return True
        return False
       
    def traktRequest(self, path, data=None, headers=None, url=None, method='GET', count=0):
        if None == url:
            url = self.api_url
       
        count = count + 1
       
        if None == headers:
            headers = self.headers
       
        if None == sickbeard.TRAKT_ACCESS_TOKEN:
            logger.log(u'You must get a Trakt TOKEN. Check your Trakt settings', logger.WARNING)
            return {}

        headers['Authorization'] = 'Bearer ' + sickbeard.TRAKT_ACCESS_TOKEN

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
                    logger.log(u'Timeout connecting to Trakt. Try to increase timeout value in Trakt settings', logger.WARNING)                      
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all                    
                else:
                    logger.log(u'Could not connect to Trakt. Error: {0}'.format(e), logger.DEBUG)                
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u'Retrying trakt api request: %s' % path, logger.DEBUG)
                return self.traktRequest(path, data, headers, url, method)
            elif code == 401:
                if self.traktToken(refresh=True, count=count):
                    return self.traktRequest(path, data, headers, url, method)
                else:
                    logger.log(u'Unauthorized. Please check your Trakt settings', logger.WARNING)
            elif code in (500,501,503,504,520,521,522):
                #http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u'Trakt may have some issues and it\'s unavailable. Try again later please', logger.DEBUG)
            elif code == 404:
                logger.log(u'Trakt error (404) the resource does not exist: %s' % url + path, logger.ERROR)
            else:
                logger.log(u'Could not connect to Trakt. Code error: {0}'.format(code), logger.ERROR)
            return {}

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise traktException(resp['message'])
            if 'error' in resp:
                raise traktException(resp['error'])
            else:
                raise traktException('Unknown Error')

        return resp
