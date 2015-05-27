from lib import requests
import json
import sickbeard
import time
from sickbeard import logger

from exceptions import traktException, traktAuthException, traktServerBusy

class TraktAPI():
    def __init__(self, disable_ssl_verify=False, timeout=30):
        self.verify = not disable_ssl_verify
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
        
    def traktRequest(self, path, data=None, headers=None, url=None, method='GET',count=0):
        if None == url:
            url = self.api_url + path
        else:
            url = url + path
        
        count = count + 1
        
        if None == headers:
            headers = self.headers
        
        if not None == sickbeard.TRAKT_ACCESS_TOKEN:
            headers['Authorization'] = 'Bearer ' + sickbeard.TRAKT_ACCESS_TOKEN
        
        try:
            resp = requests.request(method, url, headers=headers, timeout=self.timeout,
                data=json.dumps(data) if data else [], verify=self.verify)

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except requests.RequestException as e:
            code = getattr(e.response, 'status_code', None)
            if not code:
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                raise traktException(e)
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.log(u'Retrying trakt api request: %s' % path, logger.WARNING)
                return self.traktRequest(path, data, headers, method)
            elif code == 401:
                logger.log(u'Unauthorized. Please check your Trakt settings', logger.WARNING)
                if self.traktToken(refresh=True,count=count):
                    return self.traktRequest(path, data, url, method)
                raise traktAuthException(e)
            elif code in (500,501,503,504,520,521,522):
                #http://docs.trakt.apiary.io/#introduction/status-codes
                logger.log(u'Trakt may have some issues and it\'s unavailable. Try again later please', logger.WARNING)
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
