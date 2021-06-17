from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import handle_hashes
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.request import Request


class SyncMainDataDictionary(Dictionary):
    """Response for :meth:`~SyncAPIMixIn.sync_maindata`"""


class SyncTorrentPeersDictionary(Dictionary):
    """Response for :meth:`~SyncAPIMixIn.sync_torrent_peers`"""


class Sync(ClientCache):
    """
    Alows interaction with the "Sync" API endpoints.

    Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'sync_' prepended)
        >>> maindata = client.sync.maindata(rid="...")
        >>> # for use when continuously calling maindata for changes in torrents
        >>> # this will automatically request the changes since the last call
        >>> md = client.sync.maindata.delta()
        >>> #
        >>> torrentPeers = client.sync.torrentPeers(hash="...'", rid='...')
        >>> torrent_peers = client.sync.torrent_peers(hash="...'", rid='...')
    """

    def __init__(self, client):
        super(Sync, self).__init__(client=client)
        self.maindata = self._MainData(client=client)
        self.torrent_peers = self._TorrentPeers(client=client)
        self.torrentPeers = self.torrent_peers

    class _MainData(ClientCache):
        def __init__(self, client):
            super(Sync._MainData, self).__init__(client=client)
            self._rid = 0

        def __call__(self, rid=None, **kwargs):
            return self._client.sync_maindata(rid=rid, **kwargs)

        def delta(self, **kwargs):
            md = self._client.sync_maindata(rid=self._rid, **kwargs)
            self._rid = md.get("rid", 0)
            return md

        def reset_rid(self):
            self._rid = 0

    class _TorrentPeers(ClientCache):
        def __init__(self, client):
            super(Sync._TorrentPeers, self).__init__(client=client)
            self._rid = None

        def __call__(self, torrent_hash=None, rid=None, **kwargs):
            return self._client.sync_torrent_peers(
                torrent_hash=torrent_hash, rid=rid, **kwargs
            )

        def delta(self, torrent_hash=None, **kwargs):
            tp = self._client.sync_torrent_peers(
                torrent_hash=torrent_hash, rid=self._rid, **kwargs
            )
            self._rid = tp.get("rid", 0)
            return tp

        def reset_rid(self):
            self._rid = 0


@aliased
class SyncAPIMixIn(Request):
    """
    Implementation of all Sync API Methods.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> maindata = client.sync_maindata(rid="...")
        >>> torrent_peers = client.sync_torrent_peers(torrent_hash="...'", rid='...')
    """

    @property
    def sync(self):
        """
        Allows for transparent interaction with Sync endpoints.

        See Sync class for usage.
        :return: Transfer object
        """
        if self._sync is None:
            self._sync = Sync(client=self)
        return self._sync

    @response_json(SyncMainDataDictionary)
    @login_required
    def sync_maindata(self, rid=0, **kwargs):
        """
        Retrieves sync data.

        :param rid: response ID
        :return: :class:`SyncMainDataDictionary` - https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-main-data
        """
        data = {"rid": rid}
        return self._post(_name=APINames.Sync, _method="maindata", data=data, **kwargs)

    @Alias("sync_torrentPeers")
    @handle_hashes
    @response_json(SyncTorrentPeersDictionary)
    @login_required
    def sync_torrent_peers(self, torrent_hash=None, rid=0, **kwargs):
        """
        Retrieves torrent sync data. (alias: sync_torrentPeers)

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :param rid: response ID
        :return: :class:`SyncTorrentPeersDictionary` - https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-peers-data
        """
        data = {"hash": torrent_hash, "rid": rid}
        return self._post(
            _name=APINames.Sync, _method="torrentPeers", data=data, **kwargs
        )
