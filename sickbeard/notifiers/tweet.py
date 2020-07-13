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
import sickbeard
from sickbeard import common, logger


class Notifier(object):
    consumer_key = b'vHHtcB6WzpWDG6KYlBMr8g'
    consumer_hash = b'zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E'  # (consumer_secret)

    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

    def notify_snatch(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONSNATCH:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version='??'):
        if sickbeard.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + ' - ' + update_text + new_version)

    def notify_login(self, ipaddress=''):
        if sickbeard.USE_TWITTER:
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
            sickbeard.TWITTER_USERNAME = request_token['oauth_token']
            sickbeard.TWITTER_PASSWORD = request_token['oauth_token_secret']
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
                                      resource_owner_key=sickbeard.TWITTER_USERNAME,
                                      resource_owner_secret=sickbeard.TWITTER_PASSWORD)

        try:
            access_token = oauth_session.fetch_access_token(self.ACCESS_TOKEN_URL, verifier=str(key))
        except Exception as err:
            logger.exception('The request for a token with did not succeed: {}'.format(err))
            return False

        logger.debug('Your Twitter Access Token key: {0}'.format(access_token['oauth_token']))
        logger.debug('Access Token secret: {0}'.format(access_token['oauth_token_secret']))
        sickbeard.TWITTER_USERNAME = access_token['oauth_token']
        sickbeard.TWITTER_PASSWORD = access_token['oauth_token_secret']
        return True

    def _send_tweet(self, message=None):
        """
        Sends a tweet.

        :param message: Message to send
        :return: True if succeeded, False otherwise
        """
        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_hash,
                          access_token_key=sickbeard.TWITTER_USERNAME,
                          access_token_secret=sickbeard.TWITTER_PASSWORD)

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
        dmdest = sickbeard.TWITTER_DMTO

        api = twitter.Api(consumer_key=self.consumer_key,
                          consumer_secret=self.consumer_hash,
                          access_token_key=sickbeard.TWITTER_USERNAME,
                          access_token_secret=sickbeard.TWITTER_PASSWORD)

        logger.debug("Sending DM @{0}: {1}".format(dmdest, message))
        try:
            api.PostDirectMessage(message[:139], screen_name=dmdest)
        except Exception as e:
            logger.exception("Error Sending Tweet (DM): {}".format(str(e)))
            return False

        return True

    def _notifyTwitter(self, message='', force=False):
        prefix = sickbeard.TWITTER_PREFIX

        if not sickbeard.USE_TWITTER and not force:
            return False

        if sickbeard.TWITTER_USEDM and sickbeard.TWITTER_DMTO:
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)
