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

        log_string = f"{self.name}: Requested a {method.upper()} connection to url {self.url}"

        if params:
            log_string += f"?{urlencode(params)}"

        if data:
            log_string += f" and data: {str(data)[0:99]}{'...' if len(str(data)) > 100 else ''}"

        logger.debug(log_string)

        if not (self.auth or self._get_auth()):
            logger.warning(f"{self.name}: Authentication Failed")
            return False

        try:
            self.response = self.session.request(method.upper(), self.url, params=params, data=data, files=files, cookies=cookies, timeout=120, verify=False)

            self.response.raise_for_status()
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False

        logger.debug(f"{self.name}: Response to the {method.upper()} request is {self.response.text}")

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
                logger.info(f"Error is: {error}")
                logger.info(f"Torrent bencoded data: {result.content!r}")
                raise

            try:
                info = torrent_bdecode[b"info"]
            except Exception:
                logger.exception("Unable to find info field in torrent")
                logger.info(f"Torrent bencoded data: {result.content!r}")
                raise

            try:
                result.hash = sha1(bencodepy.encode(info)).hexdigest()
                logger.debug(f"Result Hash is {result.hash}")
            except (bencodepy.BencodeDecodeError, Exception) as error:
                logger.exception("Unable to bencode torrent info")
                logger.info(f"Error is: {error}")
                logger.info(f"Torrent bencoded data: {result.content!r}")
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
            logger.warning(f"{self.name}: Authentication Failed")
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
                logger.warning(f"{self.name}: Unable to send Torrent")
                return False

            if not self._set_torrent_pause(result):
                logger.exception(f"{self.name}: Unable to set the pause for Torrent")

            if not self._set_torrent_label(result):
                logger.exception(f"{self.name}: Unable to set the label for Torrent")

            if not self._set_torrent_ratio(result):
                logger.exception(f"{self.name}: Unable to set the ratio for Torrent")

            if not self._set_torrent_seed_time(result):
                logger.exception(f"{self.name}: Unable to set the seed time for Torrent")

            if not self._set_torrent_path(result):
                logger.exception(f"{self.name}: Unable to set the path for Torrent")

            if result.priority != 0 and not self._set_torrent_priority(result):
                logger.exception(f"{self.name}: Unable to set priority for Torrent")

        except Exception as error:
            logger.exception(f"{self.name}: Failed Sending Torrent")
            logger.debug(f"{self.name}: Exception raised when sending torrent: {result}. Error {error}")
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
                return False, f"Failed to authenticate with {self.name}"
        except Exception as error:
            helpers.handle_requests_exception(error)
            return False, f"{error}"
