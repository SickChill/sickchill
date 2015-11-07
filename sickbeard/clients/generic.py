# coding=utf-8

import re
import time
from hashlib import sha1
from base64 import b16encode, b32decode

import sickbeard
from sickbeard import logger
from sickbeard.clients import http_error_code
from bencode import bencode, bdecode
import requests
from bencode.BTL import BTFailure


class GenericClient(object):
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
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def _request(self, method='get', params=None, data=None, files=None):

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
            self.response = self.session.__getattribute__(method)(self.url, params=params, data=data, files=files,
                                                                  timeout=120, verify=False)
        except requests.exceptions.ConnectionError, e:
            logger.log(self.name + u': Unable to connect ' + str(e), logger.ERROR)
            return False
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL):
            logger.log(self.name + u': Invalid Host', logger.ERROR)
            return False
        except requests.exceptions.HTTPError, e:
            logger.log(self.name + u': Invalid HTTP Request ' + str(e), logger.ERROR)
            return False
        except requests.exceptions.Timeout, e:
            logger.log(self.name + u': Connection Timeout ' + str(e), logger.WARNING)
            return False
        except Exception, e:
            logger.log(self.name + u': Unknown exception raised when send torrent to ' + self.name + ': ' + str(e),
                       logger.ERROR)
            return False

        if self.response.status_code == 401:
            logger.log(self.name + u': Invalid Username or Password, check your config', logger.ERROR)
            return False

        if self.response.status_code in http_error_code.keys():
            logger.log(self.name + u': ' + http_error_code[self.response.status_code], logger.DEBUG)
            return False

        logger.log(self.name + u': Response to ' + method.upper() + ' request is ' + self.response.text, logger.DEBUG)

        return True

    def _get_auth(self):
        """
        This should be overridden and should return the auth_id needed for the client
        """
        return None

    def _add_torrent_uri(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via url (magnet or .torrent link)
        """
        return False

    def _add_torrent_file(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is added via result.content (only .torrent file)
        """
        return False

    def _set_torrent_label(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with label
        """
        return True

    def _set_torrent_ratio(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with ratio
        """
        return True

    def _set_torrent_seed_time(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with a seed time
        """
        return True

    def _set_torrent_priority(self, result):
        """
        This should be overriden should return the True/False from the client
        when a torrent is set with result.priority (-1 = low, 0 = normal, 1 = high)
        """
        return True

    def _set_torrent_path(self, torrent_path):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with path
        """
        return True

    def _set_torrent_pause(self, result):
        """
        This should be overridden should return the True/False from the client
        when a torrent is set with pause
        """
        return True

    def _get_torrent_hash(self, result):

        if result.url.startswith('magnet'):
            result.hash = re.findall(r'urn:btih:([\w]{32,40})', result.url)[0]
            if len(result.hash) == 32:
                result.hash = b16encode(b32decode(result.hash)).lower()
        else:
            if not result.content:
                logger.log(u'Torrent without content', logger.ERROR)
                raise Exception('Torrent without content')

            try:
                torrent_bdecode = bdecode(result.content)
            except BTFailure:
                logger.log(u'Unable to bdecode torrent', logger.ERROR)
                logger.log(u'Torrent bencoded data: %r' % result.content, logger.DEBUG)
                raise
            try:
                info = torrent_bdecode["info"]
            except Exception:
                logger.log(u'Unable to find info field in torrent', logger.ERROR)
                raise
            result.hash = sha1(bencode(info)).hexdigest()

        return result

    def sendTORRENT(self, result):

        r_code = False

        logger.log(u'Calling ' + self.name + ' Client', logger.DEBUG)

        if not self._get_auth():
            logger.log(self.name + u': Authentication Failed', logger.ERROR)
            return r_code

        try:
            # Sets per provider seed ratio
            result.ratio = result.provider.seedRatio()

            # lazy fix for now, I'm sure we already do this somewhere else too
            result = self._get_torrent_hash(result)

            if result.url.startswith('magnet'):
                r_code = self._add_torrent_uri(result)
            else:
                r_code = self._add_torrent_file(result)

            if not r_code:
                logger.log(self.name + u': Unable to send Torrent: Return code undefined', logger.ERROR)
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

        except Exception, e:
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
