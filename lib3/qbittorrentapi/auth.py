from logging import getLogger

from qbittorrentapi.decorators import login_required
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.exceptions import LoginFailed
from qbittorrentapi.request import Request

logger = getLogger(__name__)


class Authorization(ClientCache):
    """
    Allows interaction with the "Authorization" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> client.auth.is_logged_in
        >>> client.auth.log_in(username='admin', password='adminadmin')
        >>> client.auth.log_out()
    """

    @property
    def is_logged_in(self):
        """Implements :meth:`~AuthAPIMixIn.is_logged_in`"""
        return self._client.is_logged_in

    def log_in(self, username=None, password=None):
        """Implements :meth:`~AuthAPIMixIn.auth_log_in`"""
        return self._client.auth_log_in(username=username, password=password)

    def log_out(self):
        """Implements :meth:`~AuthAPIMixIn.auth_log_out`"""
        return self._client.auth_log_out()


class AuthAPIMixIn(Request):
    """
    Implementation of all Authorization API methods.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> client.auth_is_logged_in()
        >>> client.auth_log_in(username='admin', password='adminadmin')
        >>> client.auth_log_out()
    """

    @property
    def auth(self):
        """
        Allows for transparent interaction with Authorization endpoints.

        :return: Auth object
        """
        if self._authorization is None:
            self._authorization = Authorization(client=self)
        return self._authorization

    authorization = auth

    @property
    def is_logged_in(self):
        """
        Returns True/False for whether a log-in attempt was ever successfully completed.

        It isn't possible to know if qBittorrent will accept whatever SID is locally
        cached...however, any request that is rejected because of the SID will be automatically
        retried after a new SID is requested.

        :returns: True/False for whether a log-in attempt was previously completed
        """
        return bool(self._SID)

    def auth_log_in(self, username=None, password=None, **kwargs):
        """
        Log in to qBittorrent host.

        :raises LoginFailed: if credentials failed to log in
        :raises Forbidden403Error: if user user is banned...or not logged in

        :param username: user name for qBittorrent client
        :param password: password for qBittorrent client
        :return: None
        """
        if username:
            self.username = username or ""
            self._password = password or ""

        self._initialize_context()
        self._post(
            _name=APINames.Authorization,
            _method="login",
            data={"username": self.username, "password": self._password},
            **kwargs
        )

        if not self.is_logged_in:
            logger.debug('Login failed for user "%s"' % self.username)
            raise self._suppress_context(
                LoginFailed('Login authorization failed for user "%s"' % self.username)
            )
        else:
            logger.debug('Login successful for user "%s"' % self.username)
            logger.debug("SID: %s" % self._SID)

    @property
    def _SID(self):
        """
        Authorization cookie from qBittorrent.

        :return: SID auth cookie from qBittorrent or None if one isn't already acquired
        """
        if self._requests_session:
            return self._requests_session.cookies.get("SID", None)
        return None

    @login_required
    def auth_log_out(self, **kwargs):
        """
        End session with qBittorrent.
        """
        self._get(_name=APINames.Authorization, _method="logout", **kwargs)
