from logging import getLogger
from json import dumps

from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import endpoint_introduced
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.decorators import response_text
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.request import Request

logger = getLogger(__name__)


class ApplicationPreferencesDictionary(Dictionary):
    """Response for :meth:`~AppAPIMixIn.app_preferences`"""


class BuildInfoDictionary(Dictionary):
    """Response for :meth:`~AppAPIMixIn.app_build_info`"""


@aliased
class Application(ClientCache):
    """
    Allows interaction with "Application" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'app_' prepended)
        >>> webapiVersion = client.application.webapiVersion
        >>> web_api_version = client.application.web_api_version
        >>> app_web_api_version = client.application.app_web_api_version
        >>> # access and set preferences as attributes
        >>> is_dht_enabled = client.application.preferences.dht
        >>> # supports sending a just subset of preferences to update
        >>> client.application.preferences = dict(dht=(not is_dht_enabled))
        >>> prefs = client.application.preferences
        >>> prefs['web_ui_clickjacking_protection_enabled'] = True
        >>> client.app.preferences = prefs
        >>>
        >>> client.application.shutdown()
    """

    @property
    def version(self):
        """Implements :meth:`~AppAPIMixIn.app_version`"""
        return self._client.app_version()

    @property
    def web_api_version(self):
        """Implements :meth:`~AppAPIMixIn.app_web_api_version`"""
        return self._client.app_web_api_version()

    webapiVersion = web_api_version

    @property
    def build_info(self):
        """Implements :meth:`~AppAPIMixIn.app_build_info`"""
        return self._client.app_build_info()

    buildInfo = build_info

    def shutdown(self):
        """Implements :meth:`~AppAPIMixIn.app_shutdown`"""
        return self._client.app_shutdown()

    @property
    def preferences(self):
        """Implements :meth:`~AppAPIMixIn.app_preferences` and :meth:`~AppAPIMixIn.app_set_preferences`"""
        return self._client.app_preferences()

    @preferences.setter
    def preferences(self, v):
        """Implements :meth:`~AppAPIMixIn.app_set_preferences`"""
        self.set_preferences(prefs=v)

    @Alias("setPreferences")
    def set_preferences(self, prefs=None, **kwargs):
        """Implements :meth:`~AppAPIMixIn.app_set_preferences`"""
        return self._client.app_set_preferences(prefs=prefs, **kwargs)

    @property
    def default_save_path(self, **kwargs):
        """Implements :meth:`~AppAPIMixIn.app_default_save_path`"""
        return self._client.app_default_save_path(**kwargs)

    defaultSavePath = default_save_path


@aliased
class AppAPIMixIn(Request):
    """
    Implementation of all Application API methods

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> client.app_version()
        >>> client.app_preferences()
    """

    @property
    def app(self):
        """
        Allows for transparent interaction with Application endpoints. (alias: app)

        See Application class for usage.
        :return: Application object
        """
        if self._application is None:
            self._application = Application(client=self)
        return self._application

    application = app

    @response_text(str)
    @login_required
    def app_version(self, **kwargs):
        """
        Retrieve application version

        :return: string
        """
        return self._get(_name=APINames.Application, _method="version", **kwargs)

    @Alias("app_webapiVersion")
    @response_text(str)
    @login_required
    def app_web_api_version(self, **kwargs):
        """
        Retrieve web API version. (alias: app_webapiVersion)

        :return: string
        """
        if self._MOCK_WEB_API_VERSION:
            return self._MOCK_WEB_API_VERSION
        return self._get(_name=APINames.Application, _method="webapiVersion", **kwargs)

    @endpoint_introduced("2.3", "app/buildInfo")
    @response_json(BuildInfoDictionary)
    @Alias("app_buildInfo")
    @login_required
    def app_build_info(self, **kwargs):
        """
        Retrieve build info. (alias: app_buildInfo)

        :return: :class:`BuildInfoDictionary` - https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-build-info
        """
        return self._get(_name=APINames.Application, _method="buildInfo", **kwargs)

    @login_required
    def app_shutdown(self, **kwargs):
        """
        Shutdown qBittorrent.
        """
        self._post(_name=APINames.Application, _method="shutdown", **kwargs)

    @response_json(ApplicationPreferencesDictionary)
    @login_required
    def app_preferences(self, **kwargs):
        """
        Retrieve qBittorrent application preferences.

        :return: :class:`ApplicationPreferencesDictionary` - https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-application-preferences
        """
        return self._get(_name=APINames.Application, _method="preferences", **kwargs)

    @Alias("app_setPreferences")
    @login_required
    def app_set_preferences(self, prefs=None, **kwargs):
        """
        Set one or more preferences in qBittorrent application. (alias: app_setPreferences)

        :param prefs: dictionary of preferences to set
        :return: None
        """
        data = {"json": dumps(prefs, separators=(",", ":"))}
        self._post(
            _name=APINames.Application, _method="setPreferences", data=data, **kwargs
        )

    @Alias("app_defaultSavePath")
    @response_text(str)
    @login_required
    def app_default_save_path(self, **kwargs):
        """
        Retrieves the default path for where torrents are saved. (alias: app_defaultSavePath)

        :return: string
        """
        return self._get(
            _name=APINames.Application, _method="defaultSavePath", **kwargs
        )
