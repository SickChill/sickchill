import re
from xml.etree import ElementTree

from requests.structures import CaseInsensitiveDict

import sickchill.oldbeard.common
from sickchill import logger, settings
from sickchill.oldbeard import common
from sickchill.oldbeard.helpers import getURL, make_session


class Notifier(object):
    def __init__(self):
        self.headers = CaseInsensitiveDict(
            {
                "X-Plex-Device-Name": "SickChill",
                "X-Plex-Product": "SickChill Notifier",
                "X-Plex-Client-Identifier": sickchill.oldbeard.common.USER_AGENT,
                "X-Plex-Version": "2016.02.10",
            }
        )
        self.session = make_session()

    @staticmethod
    def _notify_pht(message, title="SickChill", host=None, username=None, password=None, force=False):
        """Internal wrapper for the notify_snatch and notify_download functions

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            host: Plex Home Theater(s) host:port
            username: Plex username
            password: Plex password
            force: Used for the Test method to override config safety checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not settings.USE_PLEX_CLIENT and not force:
            return False

        host = host or settings.PLEX_CLIENT_HOST
        username = username or settings.PLEX_CLIENT_USERNAME
        password = password or settings.PLEX_CLIENT_PASSWORD

        return sickchill.oldbeard.notifiers.kodi_notifier._notify_kodi(
            message, title=title, host=host, username=username, password=password, force=force, dest_app="PLEX"
        )

    ##############################################################################
    # Public functions
    ##############################################################################

    def notify_snatch(self, ep_name):
        if settings.PLEX_NOTIFY_ONSNATCH:
            self._notify_pht(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if settings.PLEX_NOTIFY_ONDOWNLOAD:
            self._notify_pht(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_pht(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_update(self, new_version="??"):
        if settings.NOTIFY_ON_UPDATE:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            if update_text and title and new_version:
                self._notify_pht(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if settings.NOTIFY_ON_LOGIN:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            if update_text and title and ipaddress:
                self._notify_pht(update_text.format(ipaddress), title)

    def test_notify_pht(self, host, username, password):
        return self._notify_pht("This is a test notification from SickChill", "Test Notification", host, username, password, force=True)

    def test_notify_pms(self, host, username, password, plex_server_token):
        return self.update_library(host=host, username=username, password=password, plex_server_token=plex_server_token, force=True)

    def update_library(self, ep_obj=None, host=None, username=None, password=None, plex_server_token=None, force=False):
        """Handles updating the Plex Media Server host via HTTP API

        Plex Media Server currently only supports updating the whole video library and not a specific path.

        Returns:
            Returns None for no issue, else a string of host with connection issues

        """

        if not (settings.USE_PLEX_SERVER and settings.PLEX_UPDATE_LIBRARY) and not force:
            return None

        host = host or settings.PLEX_SERVER_HOST
        if not host:
            logger.debug("PLEX: No Plex Media Server host specified, check your settings")
            return False

        if not self.get_token(username, password, plex_server_token):
            logger.warning("PLEX: Error getting auth token for Plex Media Server, check your settings")
            return False

        file_location = "" if not ep_obj else ep_obj.location
        host_list = {x.strip() for x in host.split(",") if x.strip()}
        hosts_all = hosts_match = {}
        hosts_failed = set()

        for cur_host in host_list:

            url = "http{0}://{1}/library/sections".format(("", "s")[settings.PLEX_SERVER_HTTPS], cur_host)
            try:
                xml_response = getURL(url, headers=self.headers, session=self.session, returns="text", verify=False, allow_proxy=False)
                if not xml_response:
                    logger.warning("PLEX: Error while trying to contact Plex Media Server: {0}".format(cur_host))
                    hosts_failed.add(cur_host)
                    continue

                media_container = ElementTree.fromstring(xml_response)
            except IOError as error:
                logger.warning(f"PLEX: Error while trying to contact Plex Media Server: {error}")
                hosts_failed.add(cur_host)
                continue
            except Exception as error:
                if "invalid token" in f"{error}":
                    logger.warning("PLEX: Please set TOKEN in Plex settings: ")
                else:
                    logger.warning(f"PLEX: Error while trying to contact Plex Media Server: {error}")
                hosts_failed.add(cur_host)
                continue

            sections = media_container.findall(".//Directory")
            if not sections:
                logger.debug(f"PLEX: Plex Media Server not running on: {cur_host}")
                hosts_failed.add(cur_host)
                continue

            for section in sections:
                if "show" == section.attrib["type"]:

                    keyed_host = [(str(section.attrib["key"]), cur_host)]
                    hosts_all.update(keyed_host)
                    if not file_location:
                        continue

                    for section_location in section.findall(".//Location"):
                        section_path = re.sub(r"[/\\]+", "/", section_location.attrib["path"].lower())
                        section_path = re.sub(r"^(.{,2})[/\\]", "", section_path)
                        location_path = re.sub(r"[/\\]+", "/", file_location.lower())
                        location_path = re.sub(r"^(.{,2})[/\\]", "", location_path)

                        if section_path in location_path:
                            hosts_match.update(keyed_host)

        if force:
            return (", ".join(set(hosts_failed)), None)[not len(hosts_failed)]

        if hosts_match:
            logger.debug("PLEX: Updating hosts where TV section paths match the downloaded show: " + ", ".join(set(hosts_match)))
        else:
            logger.debug("PLEX: Updating all hosts with TV sections: " + ", ".join(set(hosts_all)))

        hosts_try = (hosts_match.copy(), hosts_all.copy())[not len(hosts_match)]
        for section_key, cur_host in hosts_try.items():

            url = "http{0}://{1}/library/sections/{2}/refresh".format(("", "s")[settings.PLEX_SERVER_HTTPS], cur_host, section_key)
            try:
                getURL(url, headers=self.headers, session=self.session, returns="text", verify=False, allow_proxy=False)
            except Exception as error:
                logger.warning(f"PLEX: Error updating library section for Plex Media Server: {error}")
                hosts_failed.add(cur_host)

        return (", ".join(set(hosts_failed)), None)[not len(hosts_failed)]

    def get_token(self, username=None, password=None, plex_server_token=None):
        username = username or settings.PLEX_SERVER_USERNAME
        password = password or settings.PLEX_SERVER_PASSWORD
        plex_server_token = plex_server_token or settings.PLEX_SERVER_TOKEN

        if plex_server_token:
            self.headers["X-Plex-Token"] = plex_server_token

        if "X-Plex-Token" in self.headers:
            return True

        if not (username and password):
            return True

        logger.debug("PLEX: fetching plex.tv credentials for user: " + username)

        params = {"user[login]": username, "user[password]": password}

        try:
            response = getURL(
                "https://plex.tv/users/sign_in.json", post_data=params, headers=self.headers, session=self.session, returns="json", allow_proxy=False
            )

            self.headers["X-Plex-Token"] = response["user"]["authentication_token"]

        except Exception as error:
            self.headers.pop("X-Plex-Token", "")
            logger.debug("PLEX: Error fetching credentials from from plex.tv for user {0}: {1}".format(username, error))

        return "X-Plex-Token" in self.headers
