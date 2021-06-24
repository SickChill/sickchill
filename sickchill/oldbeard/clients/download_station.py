#
# Uses the Synology Download Station API:
# http://download.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf

import re
from json import JSONDecodeError
from urllib.parse import unquote, urljoin

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient
from sickchill.providers.GenericProvider import GenericProvider


class Client(GenericClient):
    """
    Class to send torrents/NZBs or links to them to DownloadStation
    """

    def __init__(self, host=None, username=None, password=None):
        """
        Initializes the DownloadStation client
        params: :host: Url to the Download Station API
                :username: Username to use for authentication
                :password: Password to use for authentication
        """
        super().__init__("DownloadStation", host, username, password)

        self.urls = {
            "login": urljoin(self.host, "webapi/auth.cgi"),
            "task": urljoin(self.host, "webapi/entry.cgi"),
            "info": urljoin(self.host, "webapi/DownloadStation/info.cgi"),
        }

        self.url = self.urls["task"]

        generic_errors = {
            100: "Unknown error",
            101: "Invalid parameter",
            102: "The requested API does not exist",
            103: "The requested method does not exist",
            104: "The requested version does not support the functionality",
            105: "The logged in session does not have permission",
            106: "Session timeout",
            107: "Session interrupted by duplicate login",
        }
        self.error_map = {
            "create": {
                400: "File upload failed",
                401: "Max number of tasks reached",
                402: "Destination denied",
                403: "Destination does not exist",
                404: "Invalid task id",
                405: "Invalid task action",
                406: "No default destination",
                407: "Set destination failed",
                408: "File does not exist",
            },
            "login": {
                400: "No such account or incorrect password",
                401: "Account disabled",
                402: "Permission denied",
                403: "2-step verification code required",
                404: "Failed to authenticate 2-step verification code",
            },
        }
        for api_method in self.error_map:
            self.error_map[api_method].update(generic_errors)

        self._task_post_data = {
            "api": "SYNO.DownloadStation2.Task",
            "version": "2",
            "method": "create",
            "session": "DownloadStation",
        }

    def _get_auth(self):
        """
        Authenticates the session with DownloadStation
        """
        if self.session.cookies and self.auth:
            return self.auth

        params = {
            "api": "SYNO.API.Auth",
            "version": 6,
            "method": "login",
            "account": self.username,
            "passwd": self.password,
            "session": "DownloadStation",
            "format": "cookie",
        }

        self.response = self.session.get(self.urls["login"], params=params, verify=False)

        self.auth = self._check_response()
        return self.auth

    def _check_response(self, data=None):
        """
        Checks the response from Download Station, and logs any errors
        params: :data: post data sent in the original request, in case we need to send it with adjusted parameters
                :file: file data being sent with the post request, if any
        """
        try:
            jdata = self.response.json()
        except (ValueError, AttributeError):
            logger.info("Could not convert response to json, check the host:port: {0!r}".format(self.response))
            return False

        if not jdata.get("success"):
            error_code = jdata.get("error", {}).get("code")
            api_method = (data or {}).get("method", "login")
            log_string = self.error_map.get(api_method).get(error_code, None)
            if not log_string:
                logger.info(jdata)
            else:
                logger.info("{0}".format(log_string))

        return jdata.get("success")

    def _get_destination(self, result):
        """
        Determines which destination setting to use depending on result type
        """
        if result.resultType in (GenericProvider.NZB, GenericProvider.NZBDATA):
            destination = settings.SYNOLOGY_DSM_PATH.strip()
        elif result.resultType == GenericProvider.TORRENT:
            destination = settings.TORRENT_PATH.strip()
        else:
            raise AttributeError("Invalid result passed to client when getting destination: resultType {}".format(result.resultType))

        return re.sub(r"^/volume\d/", "", destination).lstrip("/")

    def _set_destination(self, result, destination):
        """
        Determines which destination setting to use depending on result type and sets it to `destination`
        params: :destination: DSM share name
        """
        destination = destination.strip()
        if result.resultType in (GenericProvider.NZB, GenericProvider.NZBDATA):
            settings.SYNOLOGY_DSM_PATH = destination
        elif result.resultType == GenericProvider.TORRENT:
            settings.TORRENT_PATH = destination
        else:
            raise AttributeError("Invalid result passed to client when setting destination")

    def _check_destination(self, result):
        """
        If destination is not set in configuration, grab it from the API
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        params = {
            "api": "SYNO.DownloadStation.Info",
            "version": "2",
            "method": "getconfig",
        }

        if not self._get_destination(result):
            try:
                response = self.session.get(self.urls["info"], params=params, verify=False)
                response_json = response.json()
                self._set_destination(result, response_json["data"]["default_destination"])
                logger.info("Destination set to %s", self._get_destination(result))
            except (ValueError, KeyError, JSONDecodeError) as error:
                logger.debug("Get DownloadStation default destination error: {0}".format(error))
                logger.warning("Could not get share destination from DownloadStation for {}, please set it in the settings", result.resultType)
                raise

    def _add_torrent_uri(self, result):
        """
        Sends a magnet, Torrent url or NZB url to DownloadStation
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        self._check_destination(result)

        data = self._task_post_data

        if "%3A%2F%2F" in result.url:
            data["url"] = unquote(result.url)
        else:
            data["url"] = result.url

        data["type"] = "url"
        data["create_list"] = "false"
        data["destination"] = self._get_destination(result)

        logger.info('Posted as url with {} destination "{}"'.format(data["api"], data["destination"]))
        self._request(method="post", data=data)
        return self._check_response(data)

    def _add_torrent_file(self, result):
        """
        Sends a Torrent file or NZB file to DownloadStation
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        self._check_destination(result)

        data = self._task_post_data

        result_type = result.resultType.replace("data", "")
        files = {result_type: (".".join([result.name, result_type]), result.content)}

        data["type"] = '"file"'
        data["file"] = f'["{result_type}"]'
        data["create_list"] = "false"
        data["destination"] = f'"{self._get_destination(result)}"'

        logger.info("Posted as file with {} destination {}".format(data["api"], data["destination"]))
        self._request(method="post", data=data, files=files)
        return self._check_response(data)

    def sendNZB(self, result):
        """
        Sends an NZB to DownloadStation
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        logger.debug(f"Calling {self.name} Client")

        if not (self.auth or self._get_auth()):
            logger.warning("{0}: Authentication Failed".format(self.name))
            return False

        if result.resultType == "nzb":
            return self._add_torrent_uri(result)
        elif result.resultType == "nzbdata":
            return self._add_torrent_file(result)
