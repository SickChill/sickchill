from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import List, ListEntry
from qbittorrentapi.request import Request


class LogPeersList(List):
    def __init__(self, list_entries=None, client=None):
        super(LogPeersList, self).__init__(list_entries, entry_class=LogPeer, client=client)


class LogPeer(ListEntry):
    pass


class LogMainList(List):
    def __init__(self, list_entries=None, client=None):
        super(LogMainList, self).__init__(list_entries, entry_class=LogEntry, client=client)


class LogEntry(ListEntry):
    pass


class Log(ClientCache):
    """
    Allows interaction with "Log" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this is all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'log_' prepended)
        >>> log_list = client.log.main()
        >>> peers_list = client.log.peers(hash='...')
        >>> # can also filter log down with additional attributes
        >>> log_info = client.log.main.info(last_known_id='...')
        >>> log_warning = client.log.main.warning(last_known_id='...')
    """

    def __init__(self, client):
        super(Log, self).__init__(client=client)
        self.main = Log._Main(client=client)

    def peers(self, last_known_id=None, **kwargs):
        return self._client.log_peers(last_known_id=last_known_id, **kwargs)

    class _Main(ClientCache):
        def _api_call(self, normal=None, info=None, warning=None, critical=None, last_known_id=None, **kwargs):
            return self._client.log_main(normal=normal, info=info, warning=warning, critical=critical,
                                         last_known_id=last_known_id, **kwargs)

        def __call__(self, normal=None, info=None, warning=None, critical=None, last_known_id=None, **kwargs):
            return self._api_call(normal=normal, info=info, warning=warning, critial=critical,
                                  last_known_id=last_known_id, **kwargs)

        def info(self, last_known_id=None, **kwargs):
            return self._api_call(last_known_id=last_known_id, **kwargs)

        def normal(self, last_known_id=None, **kwargs):
            return self._api_call(info=False, last_known_id=last_known_id, **kwargs)

        def warning(self, last_known_id=None, **kwargs):
            return self._api_call(info=False, normal=False, last_known_id=last_known_id, **kwargs)

        def critical(self, last_known_id=None, **kwargs):
            return self._api_call(info=False, normal=False, warning=False, last_known_id=last_known_id, **kwargs)


class LogAPIMixIn(Request):
    """Implementation of all Log API methods."""

    @property
    def log(self):
        """
        Allows for transparent interaction with Log endpoints.

        See Log class for usage.
        :return: Log object
        """
        if self._log is None:
            self._log = Log(client=self)
        return self._log

    @response_json(LogMainList)
    @login_required
    def log_main(self, normal=None, info=None, warning=None, critical=None, last_known_id=None, **kwargs):
        """
        Retrieve the qBittorrent log entries. Iterate over returned object.

        :param normal: False to exclude 'normal' entries
        :param info: False to exclude 'info' entries
        :param warning: False to exclude 'warning' entries
        :param critical: False to exclude 'critical' entries
        :param last_known_id: only entries with an ID greater than this value will be returned
        :return: List of log entries.
        """
        parameters = {"normal": normal,
                      'info': info,
                      'warning': warning,
                      'critical': critical,
                      'last_known_id': last_known_id}
        return self._get(_name=APINames.Log, _method='main', params=parameters, **kwargs)

    @response_json(LogPeersList)
    @login_required
    def log_peers(self, last_known_id=None, **kwargs):
        """
        Retrieve qBittorrent peer log.

        :param last_known_id: only entries with an ID greater than this value will be returned
        :return: list of log entries in a List
        """
        parameters = {'last_known_id': last_known_id}
        return self._get(_name=APINames.Log, _method='peers', params=parameters, **kwargs)
