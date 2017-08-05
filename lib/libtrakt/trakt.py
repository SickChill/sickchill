from __future__ import unicode_literals

import json

import certifi
import requests
from oauthlib.oauth2 import TokenExpiredError
from requests.compat import urljoin
from requests_oauthlib import OAuth2Session

import sickbeard
from sickbeard import logger

from .exceptions import TraktAuthException, TraktException, TraktServerBusy


class TraktAPI(object):
    def __init__(self, ssl_verify=True, timeout=30):
        self.api_url = sickbeard.TRAKT_API_URL
        self.auth_url = urljoin(self.api_url, 'oauth/authorize')
        self.token_url = urljoin(self.api_url, 'oauth/token')

        self.verify = certifi.where() if ssl_verify else False
        self.timeout = timeout if timeout else None

        current_tokens = {}
        if sickbeard.TRAKT_ACCESS_TOKEN:
            current_tokens.update({
                'access_token': sickbeard.TRAKT_ACCESS_TOKEN,
                'refresh_token': sickbeard.TRAKT_REFRESH_TOKEN,
                'token_type': 'bearer'
            })

        self.session = OAuth2Session(
            client_id=sickbeard.TRAKT_API_KEY,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob',
            token=current_tokens
        )
        # Extra headers that Trakt API requires
        self.headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': sickbeard.TRAKT_API_KEY  # (client_id)
        }

    def get_auth_url(self):
        """ Generate an oauth url """
        auth_url, state = self.session.authorization_url(self.auth_url)
        return auth_url

    def fetch_token(self, pin_code):
        """ Authenticate using the user-supplied Trakt PIN code """
        try:
            tokens = self.session.fetch_token(
                token_url=self.token_url,
                code=pin_code,
                client_secret=sickbeard.TRAKT_API_SECRET,
                verify=self.verify,
                timeout=self.timeout
            )
            self._update_tokens(tokens)
        except Exception as error:
            logger.log('Failed to authorize Trakt: {0}'.format(error), logger.ERROR)
            return False

        return True

    def refresh_token(self):
        try:
            tokens = self.session.refresh_token(
                token_url=self.token_url,
                refresh_token=sickbeard.TRAKT_REFRESH_TOKEN,
                verify=self.verify,
                timeout=self.timeout
            )
            self._update_tokens(tokens)
        except Exception as error:
            logger.log('Failed to refresh Trakt tokens: {0}'.format(error), logger.ERROR)
            return False

        return True

    def validate_account(self):
        resp = self.trakt_request('users/settings')

        if 'account' in resp:
            return True
        return False

    def trakt_request(self, path, data=None, headers=None, url=None, method='GET', attempt=0):
        if not self.session.authorized or not sickbeard.TRAKT_ACCESS_TOKEN:
            logger.log('You are not authenticated with Trakt. Check your Trakt settings.', logger.WARNING)
            return {}

        base_url = url or self.api_url
        headers = headers or self.headers
        data = json.dumps(data) if data else []

        request_url = urljoin(base_url, path)

        if attempt > 2:
            logger.log(u'You must get a Trakt TOKEN. Check your Trakt settings', logger.WARNING)
            return {}

        attempt += 1

        try:
            resp = self.session.request(
                method=method,
                url=request_url,
                headers=headers,
                data=data,
                verify=self.verify,
                timeout=self.timeout
            )

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()

        except TokenExpiredError as err:
            # Manually refresh the tokens and try again
            logger.log('Trakt API token expired, refreshing...', logger.DEBUG)
            if self.refresh_token():
                return self.trakt_request(path, data, headers, url, method, attempt)

            logger.log('Unauthorized. Please check your Trakt settings', logger.WARNING)
            return {}

        except requests.RequestException as err:
            code = getattr(err.response, 'status_code', None)
            if not code:
                if 'timed out' in err:
                    logger.log('Timeout connecting to Trakt. Try to increase timeout value in Trakt settings',
                               logger.WARNING)
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                else:
                    logger.log('Could not connect to Trakt. Error: {0}'.format(err), logger.DEBUG)
            # Test for specific codes: (http://docs.trakt.apiary.io/#introduction/status-codes)
            elif code == 502:
                # Retry the request, Cloudflare had a proxying issue
                logger.log('Retrying Trakt API request (attempt #{0}): {1}'.format(attempt, path), logger.DEBUG)
                return self.trakt_request(path, data, headers, url, method, attempt)
            elif code == 401:
                # Manually refresh the tokens and try again
                logger.log('Trying to refresh Trakt API token...', logger.DEBUG)
                if self.refresh_token():
                    return self.trakt_request(path, data, headers, url, method, attempt)
                else:
                    logger.log('Unauthorized. Please check your Trakt settings', logger.WARNING)
            elif code in (500, 501, 503, 504, 520, 521, 522):
                logger.log('Trakt may have some issues and it\'s unavailable. Try again later please', logger.DEBUG)
            elif code == 404:
                logger.log('Trakt error (404) the resource does not exist: {0}'.format(request_url), logger.DEBUG)
            else:
                logger.log('Could not connect to Trakt. Code error: {0}'.format(code), logger.ERROR)

            return {}

        # Check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            if 'message' in resp:
                raise TraktException(resp['message'])
            if 'error' in resp:
                raise TraktException(resp['error'])
            else:
                raise TraktException('Unknown Error')

        return resp

    @staticmethod
    def _update_tokens(tokens):
        """ Update the stored access and refresh token """
        sickbeard.TRAKT_ACCESS_TOKEN = tokens['access_token']
        sickbeard.TRAKT_REFRESH_TOKEN = tokens['refresh_token']
