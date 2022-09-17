import time
from xml.etree import ElementTree

import requests

from sickchill import logger, settings


class Notifier(object):
    @staticmethod
    def notify_snatch(ep_name):
        return False
        # Not implemented: Start the scanner when snatched does not make any sense

    def notify_download(self, ep_name):
        self._notifyNMJ()

    def notify_subtitle_download(self, ep_name, lang):
        self._notifyNMJ()

    @staticmethod
    def notify_update(new_version):
        return False
        # Not implemented, no reason to start scanner.

    @staticmethod
    def notify_login(ipaddress=""):
        return False

    def test_notify(self, host):
        return self._sendNMJ(host)

    @staticmethod
    def notify_settings(host, dbloc, instance):
        """
        Retrieves the NMJv2 database location from Popcorn hour

        host: The hostname/IP of the Popcorn Hour server
        dbloc: 'local' for PCH internal hard drive. 'network' for PCH network shares
        instance: Allows for selection of different DB in case of multiple databases

        Returns: True if the settings were retrieved successfully, False otherwise
        """
        try:

            url = "http://{0}:8008/file_operation?arg0=list_user_storage_file&arg1=&arg2={1}&arg3=20&arg4=true&arg5=true&arg6=true&arg7=all&arg8=name_asc&arg9=false&arg10=false".format(
                host, instance
            )
            response = requests.get(url)
            et = ElementTree.fromstring(response.text)
            time.sleep(300.0 / 1000.0)
            for node in et.iter("path"):
                url = "http://{}:8008/metadata_database?arg0=check_database&arg1={}".format(host, node.text.replace("[=]", ""))
                response = requests.get(url)
                xml_db = ElementTree.fromstring(response.text)
                if xml_db.findtext("returnValue") == "0":
                    db_path = xml_db.findtext("database_path")
                    if dbloc == "local" and "localhost" in db_path:
                        settings.NMJv2_HOST = host
                        settings.NMJv2_DATABASE = db_path
                        return True
                    if dbloc == "network" and "://" in db_path:
                        settings.NMJv2_HOST = host
                        settings.NMJv2_DATABASE = db_path
                        return True

        except IOError as error:
            logger.warning(f"Warning: Couldn't contact popcorn hour on host {host}: {error}")
            return False
        return False

    @staticmethod
    def _sendNMJ(host):
        """
        Sends a NMJ update command to the specified machine

        host: The hostname/IP to send the request to (no port)
        database: The database to send the request to
        mount: The mount URL to use (optional)

        Returns: True if the request succeeded, False otherwise
        """

        # if a host is provided then attempt to open a handle to that URL
        try:
            url = "http://{}:8008/metadata_database?arg0=update_scandir&arg1={}&arg2=&arg3=update_all".format(host, settings.NMJv2_DATABASE)
            logger.debug("NMJ scan update command sent to host: {0}".format(host))
            response1 = requests.get(url)
            time.sleep(300.0 / 1000.0)

            url = "http://{}:8008/metadata_database?arg0=scanner_start&arg1{}&arg2=background&arg3=".format(host, settings.NMJv2_DATABASE)
            logger.debug("Try to mount network drive via url: {0}".format(host))
            response2 = requests.get(url)
        except IOError as error:
            logger.warning(f"Warning: Couldn't contact popcorn hour on host {host}: {error}")
            return False
        try:
            et = ElementTree.fromstring(response1.text)
            result1 = et.findtext("returnValue")
        except SyntaxError as error:
            logger.exception(f"Unable to parse XML returned from the Popcorn Hour: update_scandir, {error}")
            return False
        try:
            et = ElementTree.fromstring(response2.text)
            result2 = et.findtext("returnValue")
        except SyntaxError as error:
            logger.exception(f"Unable to parse XML returned from the Popcorn Hour: scanner_start, {error}")
            return False

        # if the result was a number then consider that an error
        error_codes = ["8", "11", "22", "49", "50", "51", "60"]
        error_messages = [
            "Invalid parameter(s)/argument(s)",
            "Invalid database path",
            "Insufficient size",
            "Database write error",
            "Database read error",
            "Open fifo pipe failed",
            "Read only file system",
        ]
        if int(result1) > 0:
            index = error_codes.index(result1)
            logger.exception(f"Popcorn Hour returned an error: {error_messages[index]}")
            return False
        else:
            if int(result2) > 0:
                index = error_codes.index(result2)
                logger.exception(f"Popcorn Hour returned an error: {error_messages[index]}")
                return False
            else:
                logger.info("NMJv2 started background scan")
                return True

    def _notifyNMJ(self, host=None, force=False):
        """
        Sends a NMJ update command based on the SB config settings

        host: The host to send the command to (optional, defaults to the host in the config)
        database: The database to use (optional, defaults to the database in the config)
        mount: The mount URL (optional, defaults to the mount URL in the config)
        force: If True then the notification will be sent even if NMJ is disabled in the config
        """
        if not settings.USE_NMJv2 and not force:
            logger.debug("Notification for NMJ scan update not enabled, skipping this notification")
            return False

        # fill in omitted parameters
        if not host:
            host = settings.NMJv2_HOST

        logger.debug("Sending scan command for NMJ ")

        return self._sendNMJ(host)
