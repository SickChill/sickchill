import re
import time
import traceback
from base64 import b16encode, b32decode
from hashlib import sha1
from typing import Dict, Iterable, Union
from urllib.parse import urlencode

import bencodepy
import requests

from sickchill import logger, settings
from sickchill.oldbeard import helpers


class GenericClient(object):
    def __init__(self, name, host=None, username=None, password=None):
        """
        Initializes the client
        :name: str:name of the client
        :host: str:url or ip of the client
        :username: str: username for authenticating with the client
        :password: str: password for authentication with the client
        """

        self.name = name
        self.username = username or settings.TORRENT_USERNAME
        self.password = password or settings.TORRENT_PASSWORD
        self.host = host or settings.TORRENT_HOST

        self.url = None
        self.response = None
        self.auth = None
        self.last_time = time.time()
        self.session = helpers.make_session()
        self.session.auth = (self.username, self.password)

    def _request(self, method="get", params=None, data=None, files=None, cookies=None):
        """
        Makes the actual request for the client, for everything except auth
        """

        if time.time() > self.last_time + 1800 or not self.auth:
            self.last_time = time.time()
            self._get_auth()

        log_string = "{0}: Requested a {1} connection to url {2}".format(self.name, method.upper(), self.url)

        if params:
            log_string += "?{0}".format(urlencode(params))

        if data:
            log_string += " and data: {0}{1}".format(str(data)[0:99], "..." if len(str(data)) > 100 else "")

        logger.debug(log_string)

        if not (self.auth or self._get_auth()):
            logger.warning("{0}: Authentication Failed".format(self.name))
            return False

        try:
            self.response = self.session.request(method.upper(), self.url, params=params, data=data, files=files, cookies=cookies, timeout=120, verify=False)

            self.response.raise_for_status()
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False

        logger.debug("{0}: Response to the {1} request is {2}".format(self.name, method.upper(), self.response.text))

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

    @staticmethod
    def _set_torrent_path(torrent_path):  # pylint:disable=unused-argument, no-self-use
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
        if result.url.startswith("magnet"):
            result.hash = re.findall(r"urn:btih:([\w]{32,40})", result.url)[0]
            if len(result.hash) == 32:
                result.hash = b16encode(b32decode(result.hash)).lower()
        else:
            if not result.content:
                logger.exception("Torrent without content")
                raise Exception("Torrent without content")

            try:
                torrent_bdecode: Union[Iterable, Dict] = bencodepy.decode(result.content)
            except (bencodepy.BencodeDecodeError, Exception) as error:
                logger.exception("Unable to bdecode torrent")
                logger.info("Error is: {0}".format(error))
                logger.info("Torrent bencoded data: {0!r}".format(result.content))
                raise

            try:
                info = torrent_bdecode[b"info"]
            except Exception:
                logger.exception("Unable to find info field in torrent")
                logger.info("Torrent bencoded data: {0!r}".format(result.content))
                raise

            try:
                result.hash = sha1(bencodepy.encode(info)).hexdigest()
                logger.debug("Result Hash is {0}".format(result.hash))
            except (bencodepy.BencodeDecodeError, Exception) as error:
                logger.exception("Unable to bencode torrent info")
                logger.info("Error is: {0}".format(error))
                logger.info("Torrent bencoded data: {0!r}".format(result.content))
                raise

        return result

    def sendTORRENT(self, result):
        """
        Sends the magnet, url, or torrent file content to the client
        params: :result: an instance of the searchResult class
        """

        r_code = False

        logger.debug(f"Calling {self.name} Client")

        if not (self.auth or self._get_auth()):
            logger.warning("{0}: Authentication Failed".format(self.name))
            return r_code

        try:
            # Sets per provider seed ratio
            result.ratio = result.provider.seed_ratio()

            # lazy fix for now, I'm sure we already do this somewhere else too
            result = self._get_torrent_hash(result)

            if result.url.startswith("magnet"):
                r_code = self._add_torrent_uri(result)
            else:
                r_code = self._add_torrent_file(result)

            if not r_code:
                logger.warning("{0}: Unable to send Torrent".format(self.name))
                return False

            if not self._set_torrent_pause(result):
                logger.exception("{0}: Unable to set the pause for Torrent".format(self.name))

            if not self._set_torrent_label(result):
                logger.exception("{0}: Unable to set the label for Torrent".format(self.name))

            if not self._set_torrent_ratio(result):
                logger.exception("{0}: Unable to set the ratio for Torrent".format(self.name))

            if not self._set_torrent_seed_time(result):
                logger.exception("{0}: Unable to set the seed time for Torrent".format(self.name))

            if not self._set_torrent_path(result):
                logger.exception("{0}: Unable to set the path for Torrent".format(self.name))

            if result.priority != 0 and not self._set_torrent_priority(result):
                logger.exception("{0}: Unable to set priority for Torrent".format(self.name))

        except Exception as error:
            logger.exception("{0}: Failed Sending Torrent".format(self.name))
            logger.debug("{0}: Exception raised when sending torrent: {1}. Error {2}".format(self.name, result, error))
            logger.debug(traceback.format_exc())
            return r_code

        return r_code

    def testAuthentication(self):
        """
        Tests the parameters the user has provided in the ui to see if they are correct
        """
        try:
            self.response = self.session.get(self.url, timeout=120, verify=False)
        except requests.exceptions.RequestException:
            pass

        try:
            self._get_auth()
            if not self.response:
                raise requests.exceptions.HTTPError(404, "Not Found")

            self.response.raise_for_status()
            if self.auth:
                return True, "Success: Connected and Authenticated"
            else:
                return False, "Failed to authenticate with {0}".format(self.name)
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False, f"{error}"
