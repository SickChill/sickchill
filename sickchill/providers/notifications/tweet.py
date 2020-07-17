# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# Third Party Imports
import twitter
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1Session

# First Party Imports
from sickbeard import common, logger

# Local Folder Imports
from .base import AbstractNotifier


class Notifier(AbstractNotifier):
    def __init__(self):
        super().__init__('Twitter', extra_options=('username', 'password', 'use_dm', 'dm_to', 'prefix'))
        self.consumer_key = 'vHHtcB6WzpWDG6KYlBMr8g'
        self.consumer_hash = 'zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E'  # (consumer_secret)

        self.REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
        self.ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
        self.AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

    def notify_snatch(self, name):
        if self.config('snatch'):
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + name)

    def notify_download(self, name):
        if self.config('download'):
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + name)

    def notify_subtitle_download(self, name, lang):
        if self.config('subtitle'):
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + name + ": " + lang)

    def notify_git_update(self, new_version='??'):
        if self.config('update'):
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + ' - ' + update_text + new_version)

    def notify_login(self, ipaddress=''):
        if self.config('login'):
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTwitter(title + ' - ' + update_text.format(ipaddress))

    def test_notify(self):
        """
        Tests sending notification.

        :return: True if succeeded, False otherwise
        """
        return self._notifyTwitter('This is a test notification from SickChill', force=True)

    def _get_authorization(self):
        """
        Step 1 of authorization - get app authorization url.

        :return: True if succeeded, False otherwise
        """
        logger.debug('Requesting temp token from Twitter')
        oauth_session = OAuth1Session(client_key=self.consumer_key, client_secret=self.consumer_hash)

        try:
            request_token = oauth_session.fetch_request_token(self.REQUEST_TOKEN_URL)
        except RequestException as err:
            logger.exception('Invalid response from Twitter requesting temp token: {}'.format(err))
        else:
            self.set_config('username', request_token['oauth_token'])
            self.set_config('password', request_token['oauth_token_secret'])
            return oauth_session.authorization_url(self.AUTHORIZATION_URL)

    def _get_credentials(self, key):
        logger.info('Type of key is {}'.format(type(key)))
        """
        Step 2 of authorization - poll server for access token.

        :param key: Authorization key received from twitter
        :return: True if succeeded, False otherwise
        """
        logger.debug('Generating and signing request for an access token using key ' + key)
        oauth_session = OAuth1Session(client_key=self.consumer_key,
                                      client_secret=self.consumer_hash,
                                      resource_owner_key=self.config('username'),
                                      resource_owner_secret=self.config('password'))

        try:
            access_token = oauth_session.fetch_access_token(self.ACCESS_TOKEN_URL, verifier=str(key))
        except Exception as err:
            logger.exception('The request for a token with did not succeed: {}'.format(err))
            return False

        logger.debug('Your Twitter Access Token key: {0}'.format(access_token['oauth_token']))
        logger.debug('Access Token secret: {0}'.format(access_token['oauth_token_secret']))
        self.set_config('username', access_token['oauth_token'])
        self.set_config('password', access_token['oauth_token_secret'])
        return True

    def _send_tweet(self, message=None):
        """
        Sends a tweet.

        :param message: Message to send
        :return: True if succeeded, False otherwise
        """
        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_hash,
                          access_token_key=self.config('username'),
                          access_token_secret=self.config('password'))

        logger.debug("Sending tweet: {}".format(message))
        try:
            api.PostUpdate(message[:139])
        except Exception as e:
            logger.exception("Error Sending Tweet: {}".format(str(e)))
            return False

        return True

    def _send_dm(self, message=None):
        """
        Sends a direct message.

        :param message: Message to send
        :return: True if succeeded, False otherwise
        """
        dmdest = self.config('dm_to')

        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_hash,
                          access_token_key=self.config('username'),
                          access_token_secret=self.config('password'))

        logger.debug("Sending DM @{0}: {1}".format(dmdest, message))
        try:
            api.PostDirectMessage(message[:139], screen_name=dmdest)
        except Exception as e:
            logger.exception("Error Sending Tweet (DM): {}".format(str(e)))
            return False

        return True

    def _notifyTwitter(self, message='', force=False):
        if not self.config('enabled') and not force:
            return False

        prefix = self.config('prefix')
        if self.config('use_dm') and self.config('dm_to'):
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)
