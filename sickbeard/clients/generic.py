# coding=utf-8

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

from __future__ import unicode_literals

import re
import time
from hashlib import sha1
from requests.compat import urlencode
from requests.models import HTTPError
from base64 import b16encode, b32decode
import bencode

import sickbeard
from sickbeard import logger, helpers


class GenericClient(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self, name, host=None, username=None, password=None):
        """
        Initializes the client
        :name: str:name of the client
        :host: str:url or ip of the client
        :username: str: username for authenticating with the client
        :password: str: password for authentication with the client
        """

        self.name = name
        self.username = sickbeard.TORRENT_USERNAME if not username else username
        self.password = sickbeard.TORRENT_PASSWORD if not password else password
        self.host = sickbeard.TORRENT_HOST if not host else host
        self.rpcurl = sickbeard.TORRENT_RPCURL

        self.url = None
        self.response = None
        self.auth = None
        self.last_time = time.time()
        self.session = helpers.make_session()
        self.session.auth = (self.username, self.password)

    def _request(self, method='get', params=None, data=None, files=None, cookies=None):  # pylint: disable=too-many-arguments, too-many-return-statements
        """
        Makes the actual request for the client, for everything except auth
        """

        if time.time() > self.last_time + 1800 or not self.auth:
            self.last_time = time.time()
            self._get_auth()

        log_string = '{0}: Requested a {1} connection to url {2}'.format(
            self.name, method.upper(), self.url)

        if params:
            log_string += '?{0}'.format(urlencode(params))

        if data:
            log_string += ' and data: {0}{1}'.format(
                str(data)[0:99], '...' if len(str(data)) > 100 else '')

        logger.log(log_string, logger.DEBUG)

        if not self.auth:
            logger.log('{0}: Authentication Failed'.format(self.name), logger.WARNING)
            return False

        try:
            self.response = self.session.request(
                method.upper(), self.url, params=params, data=data,
                files=files, cookies=cookies, timeout=120, verify=False)

            self.response.raise_for_status()
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False

        logger.log('{0}: Response to the {1} request is {2}'.format
                   (self.name, method.upper(), self.response.text), logger.DEBUG)

        return True

    def _get_auth(self):  # pylint:disable=no-self-use
        """
        This should be overridden and should return the auth_id needed for the client
        """
        return None

    def _add_torrent_uri(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via url (magnet or .torrent link)
        """
        return False

    def _add_torrent_file(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via result.content (only .torrent file)
        """
        return False

    def _set_torrent_label(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with label
        """
        return True

    def _set_torrent_ratio(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with ratio
        """
        return True

    def _set_torrent_seed_time(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with a seed time
        """
        return True

    def _set_torrent_priority(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overriden should return the True/False from the client
        when a torrent is set with result.priority (-1 = low, 0 = normal, 1 = high)
        """
        return True

    def _set_torrent_path(self, torrent_path):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with path
        """
        return True

    def _set_torrent_pause(self, result):  # pylint:disable=unused-argument, no-self-use
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with pause
        params: :result: an instance of the searchResult class
        """
        return True

    @staticmethod
    def _get_torrent_hash(result):
        """
        Gets the torrent hash from either the magnet or torrent file content
        params: :result: an instance of the searchResult class
        """
        if result.url.startswith('magnet'):
            result.hash = re.findall(r'urn:btih:([\w]{32,40})', result.url)[0]
            if len(result.hash) == 32:
                result.hash = b16encode(b32decode(result.hash)).lower()
        else:
            if not result.content:
                logger.log('Torrent without content', logger.ERROR)
                raise Exception('Torrent without content')

            try:
                torrent_bdecode = bencode.bdecode(result.content)
            except (bencode.BTL.BTFailure, Exception) as error:
                logger.log('Unable to bdecode torrent', logger.ERROR)
                logger.log('Error is: {0}'.format(error), logger.DEBUG)
                # logger.log('Torrent bencoded data: {0!r}'.format(result.content), logger.DEBUG)
                raise
            try:
                info = torrent_bdecode[b'info']
            except Exception:
                logger.log('Unable to find info field in torrent', logger.ERROR)
                raise

            try:
                result.hash = sha1(bencode.bencode(info)).hexdigest()
                logger.log('Result Hash is {0}'.format(result.hash), logger.DEBUG)
            except (bencode.BTL.BTFailure, Exception) as error:
                logger.log('Unable to bencode torrent info', logger.ERROR)
                logger.log('Error is: {0}'.format(error), logger.DEBUG)
                # logger.log('Torrent bencoded data: {0!r}'.format(result.content), logger.DEBUG)
                raise

        return result

    def sendTORRENT(self, result):
        """
        Sends the magnet, url, or torrent file content to the client
        params: :result: an instance of the searchResult class
        """

        r_code = False

        logger.log('Calling {0} Client'.format(self.name), logger.DEBUG)

        if not (self.auth or self._get_auth()):
            logger.log('{0}: Authentication Failed'.format(self.name), logger.WARNING)
            return r_code

        try:
            # Sets per provider seed ratio
            result.ratio = result.provider.seed_ratio()

            # lazy fix for now, I'm sure we already do this somewhere else too
            result = self._get_torrent_hash(result)

            if result.url.startswith('magnet'):
                r_code = self._add_torrent_uri(result)
            else:
                r_code = self._add_torrent_file(result)

            if not r_code:
                logger.log('{0}: Unable to send Torrent'.format(self.name), logger.WARNING)
                return False

            if not self._set_torrent_pause(result):
                logger.log('{0}: Unable to set the pause for Torrent'.format(self.name), logger.ERROR)

            if not self._set_torrent_label(result):
                logger.log('{0}: Unable to set the label for Torrent'.format(self.name), logger.ERROR)

            if not self._set_torrent_ratio(result):
                logger.log('{0}: Unable to set the ratio for Torrent'.format(self.name), logger.ERROR)

            if not self._set_torrent_seed_time(result):
                logger.log('{0}: Unable to set the seed time for Torrent'.format(self.name), logger.ERROR)

            if not self._set_torrent_path(result):
                logger.log('{0}: Unable to set the path for Torrent'.format(self.name), logger.ERROR)

            if result.priority != 0 and not self._set_torrent_priority(result):
                logger.log('{0}: Unable to set priority for Torrent'.format(self.name), logger.ERROR)

        except Exception as error:
            logger.log('{0}: Failed Sending Torrent'.format(self.name), logger.ERROR)
            logger.log('{0}: Exception raised when sending torrent: {1}. Error {2}'.format(self.name, result, error), logger.DEBUG)
            return r_code

        return r_code

    def testAuthentication(self):
        """
        Tests the parameters the user has provided in the ui to see if they are correct
        """
        try:
            self.response = self.session.get(self.url, timeout=120, verify=False)
        except Exception:
            pass

        try:
            self._get_auth()
            if not self.response:
                raise HTTPError(404, 'Not Found')

            self.response.raise_for_status()
            return True, 'Success: Connected and Authenticated'
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False, '{0}'.format(error)
