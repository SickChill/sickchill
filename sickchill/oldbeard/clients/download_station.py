#
# Uses the Synology Download Station API: http://download.synology.com/download/Document/DeveloperGuide/Synology_Download_Station_Web_API.pdf
import os
import re
from urllib.parse import unquote, urljoin

from sickchill import logger, settings
from sickchill.oldbeard.clients.generic import GenericClient


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

    def _check_response(self, data=None, files=None):
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
            if error_code == 403:
                destination = (data or {}).get("destination")
                if destination and os.path.isabs(destination):
                    data["destination"] = re.sub(r"^/volume\d/", "", destination).lstrip("/")
                    self._request(method="post", data=data, files=files)

                    try:
                        jdata = self.response.json()
                    except ValueError:
                        return False

                    if jdata.get("success"):
                        if destination == settings.SYNOLOGY_DSM_PATH:
                            settings.SYNOLOGY_DSM_PATH = data["destination"]
                        elif destination == settings.TORRENT_PATH:
                            settings.TORRENT_PATH = data["destination"]

        if not jdata.get("success"):
            error_code = jdata.get("error", {}).get("code")
            api_method = (data or {}).get("method", "login")
            log_string = self.error_map.get(api_method).get(error_code, None)
            if not log_string:
                logger.info(jdata)
            else:
                logger.info("{0}".format(log_string))

        return jdata.get("success")

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

    def _add_torrent_uri(self, result):
        """
        Sends a magnet, Torrent url or NZB url to DownloadStation
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        data = self._task_post_data

        if "%3A%2F%2F" in result.url:
            data["url"] = unquote(result.url)
        else:
            data["url"] = result.url

        data["type"] = "url"
        data['create_list'] = "false"

        if result.resultType == "torrent":
            if settings.TORRENT_PATH:
                data["destination"] = settings.TORRENT_PATH
        elif settings.SYNOLOGY_DSM_PATH:
            data["destination"] = settings.SYNOLOGY_DSM_PATH
        logger.info(data)
        self._request(method="post", data=data)
        return self._check_response(data)

    def _add_torrent_file(self, result):
        """
        Sends a Torrent file or NZB file to DownloadStation
        params: :result: an object subclassing oldbeard.classes.SearchResult
        """
        data = self._task_post_data

        data["type"] = "file"
        data["file"] = f'["{result.resultType}"]'
        data['create_list'] = "false"

        if result.resultType == "torrent":
            files = {"file": (result.name + ".torrent", result.content)}
            if settings.TORRENT_PATH:
                data["destination"] = settings.TORRENT_PATH
        else:
            files = {"file": (result.name + ".nzb", result.extraInfo[0])}
            if settings.SYNOLOGY_DSM_PATH:
                data["destination"] = settings.SYNOLOGY_DSM_PATH

        logger.info(data)
        self._request(method="post", data=data, files=files)
        return self._check_response(data, files)

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
