# coding=utf-8

import re
import time
from hashlib import sha1
from base64 import b16encode, b32decode

import sickbeard
from sickbeard import logger, helpers
from bencode import Bencoder, BencodeEncodeError, BencodeDecodeError
import requests
import cookielib
from sickrage.helper.common import http_code_description


class GenericClient(object):  # pylint: disable=too-many-instance-attributes
    def __init__(self, name, host=None, username=None, password=None):

        self.name = name
        self.username = sickbeard.TORRENT_USERNAME if username is None else username
        self.password = sickbeard.TORRENT_PASSWORD if password is None else password
        self.host = sickbeard.TORRENT_HOST if host is None else host
        self.rpcurl = sickbeard.TORRENT_RPCURL

        self.url = None
        self.response = None
        self.auth = None
        self.last_time = time.time()
        self.session = helpers.make_session()
        self.session.auth = (self.username, self.password)
        self.session.cookies = cookielib.CookieJar()

    def _request(self, method='get', params=None, data=None, files=None, cookies=None):  # pylint: disable=too-many-arguments, too-many-return-statements

        if time.time() > self.last_time + 1800 or not self.auth:
            self.last_time = time.time()
            self._get_auth()

        logger.log(
            self.name + u': Requested a ' + method.upper() + ' connection to url ' + self.url +
            ' with Params: ' + str(params) + ' Data: ' + str(data)[0:99] + ('...' if len(str(data)) > 200 else ''), logger.DEBUG)

        if not self.auth:
            logger.log(self.name + u': Authentication Failed', logger.WARNING)
            return False

        try:
            self.response = self.session.__getattribute__(method)(self.url, params=params, data=data, files=files, cookies=cookies,
                                                                  timeout=120, verify=False)
        except requests.exceptions.ConnectionError as e:
            logger.log(self.name + u': Unable to connect ' + str(e), logger.ERROR)
            return False
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            logger.log(self.name + u': Invalid Host', logger.ERROR)
            return False
        except requests.exceptions.HTTPError as e:
            logger.log(self.name + u': Invalid HTTP Request ' + str(e), logger.ERROR)
            return False
        except requests.exceptions.Timeout as e:
            logger.log(self.name + u': Connection Timeout ' + str(e), logger.WARNING)
            return False
        except Exception as e:
            logger.log(self.name + u': Unknown exception raised when send torrent to ' + self.name + ': ' + str(e),
                       logger.ERROR)
            return False

        if self.response.status_code == 401:
            logger.log(self.name + u': Invalid Username or Password, check your config', logger.ERROR)
            return False

        code_description = http_code_description(self.response.status_code)

        if code_description is not None:
            logger.log(self.name + u': ' + code_description, logger.INFO)
            return False

        logger.log(self.name + u': Response to ' + method.upper() + ' request is ' + self.response.text, logger.DEBUG)

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
        """
        return True

    @staticmethod
    def _get_torrent_hash(result):

        if result.url.startswith('magnet'):
            result.hash = re.findall(r'urn:btih:([\w]{32,40})', result.url)[0]
            if len(result.hash) == 32:
                result.hash = b16encode(b32decode(result.hash)).lower()
        else:
            if not result.content:
                logger.log(u'Torrent without content', logger.ERROR)
                raise Exception('Torrent without content')

            bencoder = Bencoder()
            try:
                torrent_bdecode = bencoder.decode(result.content)
            except (BencodeDecodeError, Exception) as error:
                logger.log(u'Unable to bdecode torrent', logger.ERROR)
                logger.log(u'Error is: {0!r}'.format(error), logger.DEBUG)
                logger.log(u'Torrent bencoded data: {0!r}'.format(result.content), logger.DEBUG)
                raise
            try:
                info = torrent_bdecode["info"]
            except Exception:
                logger.log(u'Unable to find info field in torrent', logger.ERROR)
                raise

            try:
                result.hash = sha1(bencoder.encode(info)).hexdigest()
            except (BencodeEncodeError, Exception) as error:
                logger.log(u'Unable to bencode torrent info', logger.ERROR)
                logger.log(u'Error is: {0!r}'.format(error), logger.DEBUG)
                logger.log(u'Torrent bencoded data: {0!r}'.format(result.content), logger.DEBUG)
                raise

        return result

    def sendTORRENT(self, result):

        r_code = False

        logger.log(u'Calling ' + self.name + ' Client', logger.DEBUG)

        if not (self.auth or self._get_auth()):
            logger.log(self.name + u': Authentication Failed', logger.WARNING)
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
                logger.log(self.name + u': Unable to send Torrent', logger.WARNING)
                return False

            if not self._set_torrent_pause(result):
                logger.log(self.name + u': Unable to set the pause for Torrent', logger.ERROR)

            if not self._set_torrent_label(result):
                logger.log(self.name + u': Unable to set the label for Torrent', logger.ERROR)

            if not self._set_torrent_ratio(result):
                logger.log(self.name + u': Unable to set the ratio for Torrent', logger.ERROR)

            if not self._set_torrent_seed_time(result):
                logger.log(self.name + u': Unable to set the seed time for Torrent', logger.ERROR)

            if not self._set_torrent_path(result):
                logger.log(self.name + u': Unable to set the path for Torrent', logger.ERROR)

            if result.priority != 0 and not self._set_torrent_priority(result):
                logger.log(self.name + u': Unable to set priority for Torrent', logger.ERROR)

        except Exception as e:
            logger.log(self.name + u': Failed Sending Torrent', logger.ERROR)
            logger.log(self.name + u': Exception raised when sending torrent: ' + str(result) + u'. Error: ' + str(e), logger.DEBUG)
            return r_code

        return r_code

    def testAuthentication(self):

        try:
            self.response = self.session.get(self.url, timeout=120, verify=False)
        except requests.exceptions.ConnectionError:
            return False, 'Error: ' + self.name + ' Connection Error'
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            return False, 'Error: Invalid ' + self.name + ' host'

        if self.response.status_code == 401:
            return False, 'Error: Invalid ' + self.name + ' Username or Password, check your config!'

        try:
            self._get_auth()
            if self.response.status_code == 200 and self.auth:
                return True, 'Success: Connected and Authenticated'
            else:
                return False, 'Error: Unable to get ' + self.name + ' Authentication, check your config!'
        except Exception:
            return False, 'Error: Unable to connect to ' + self.name
