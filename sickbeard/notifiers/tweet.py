# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import oauth2 as oauth
import pythontwitter as twitter
import sickbeard
from sickbeard import common, logger
from sickrage.helper.exceptions import ex

try:
    from six.moves.urllib.parse import parse_qsl
except ImportError:
    from cgi import parse_qsl



class Notifier(object):
    consumer_key = b"vHHtcB6WzpWDG6KYlBMr8g"
    consumer_hash = b"zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E" # (consumer_secret)

    REQUEST_TOKEN_URL = b'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = b'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = b'https://api.twitter.com/oauth/authorize'
    SIGNIN_URL = b'https://api.twitter.com/oauth/authenticate'

    def notify_snatch(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONSNATCH:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SNATCH] + ': ' + ep_name)

    def notify_download(self, ep_name):
        if sickbeard.TWITTER_NOTIFY_ONDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ': ' + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwitter(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + ' ' + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notifyTwitter(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTwitter(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        return self._notifyTwitter("This is a test notification from SickRage", force=True)

    def _get_authorization(self):

        signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_hash)
        oauth_client = oauth.Client(oauth_consumer)

        logger.log('Requesting temp token from Twitter', logger.DEBUG)

        resp, content = oauth_client.request(self.REQUEST_TOKEN_URL, 'GET')

        if resp['status'] != '200':
            logger.log('Invalid response from Twitter requesting temp token: {0}'.format(resp['status']), logger.ERROR)
        else:
            request_token = dict(parse_qsl(content))

            sickbeard.TWITTER_USERNAME = request_token['oauth_token']
            sickbeard.TWITTER_PASSWORD = request_token['oauth_token_secret']

            return self.AUTHORIZATION_URL + "?oauth_token=" + request_token['oauth_token']

    def _get_credentials(self, key):
        request_token = {
            'oauth_token': sickbeard.TWITTER_USERNAME,
            'oauth_token_secret': sickbeard.TWITTER_PASSWORD,
            'oauth_callback_confirmed': 'true'
        }

        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(key)

        logger.log('Generating and signing request for an access token using key ' + key, logger.DEBUG)

        signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()  # @UnusedVariable
        oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_hash)
        logger.log('oauth_consumer: ' + str(oauth_consumer), logger.DEBUG)
        oauth_client = oauth.Client(oauth_consumer, token)
        logger.log('oauth_client: ' + str(oauth_client), logger.DEBUG)
        resp, content = oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier={0}'.format(key))
        logger.log('resp, content: ' + str(resp) + ',' + str(content), logger.DEBUG)

        access_token = dict(parse_qsl(content))
        logger.log('access_token: ' + str(access_token), logger.DEBUG)

        logger.log('resp[status] = ' + str(resp['status']), logger.DEBUG)
        if resp['status'] != '200':
            logger.log('The request for a token with did not succeed: ' + str(resp['status']), logger.ERROR)
            return False
        else:
            logger.log('Your Twitter Access Token key: {0}'.format(access_token['oauth_token']), logger.DEBUG)
            logger.log('Access Token secret: {0}'.format(access_token['oauth_token_secret']), logger.DEBUG)
            sickbeard.TWITTER_USERNAME = access_token['oauth_token']
            sickbeard.TWITTER_PASSWORD = access_token['oauth_token_secret']
            return True

    def _send_tweet(self, message=None):

        username = self.consumer_key
        password = self.consumer_hash
        access_token_key = sickbeard.TWITTER_USERNAME
        access_token_secret = sickbeard.TWITTER_PASSWORD

        logger.log("Sending tweet: " + message, logger.DEBUG)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostUpdate(message.encode('utf8')[:139])
        except Exception as e:
            logger.log("Error Sending Tweet: " + ex(e), logger.ERROR)
            return False

        return True

    def _send_dm(self, message=None):

        username = self.consumer_key
        password = self.consumer_hash
        dmdest = sickbeard.TWITTER_DMTO
        access_token_key = sickbeard.TWITTER_USERNAME
        access_token_secret = sickbeard.TWITTER_PASSWORD

        logger.log("Sending DM: " + dmdest + " " + message, logger.DEBUG)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostDirectMessage(dmdest, message.encode('utf8')[:139])
        except Exception as e:
            logger.log("Error Sending Tweet (DM): " + ex(e), logger.ERROR)
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
