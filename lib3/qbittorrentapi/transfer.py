from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.decorators import response_text
from qbittorrentapi.decorators import version_implemented
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.request import Request


class TransferInfoDictionary(Dictionary):
    pass


@aliased
class Transfer(ClientCache):

    """
    Alows interaction with the "Transfer" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'transfer_' prepended)
        >>> transfer_info = client.transfer.info
        >>> # access and set download/upload limits as attributes
        >>> dl_limit = client.transfer.download_limit
        >>> # this updates qBittorrent in real-time
        >>> client.transfer.download_limit = 1024000
        >>> # update speed limits mode to alternate or not
        >>> client.transfer.speedLimitsMode = True
    """

    @property
    def info(self):
        return self._client.transfer_info()

    @property
    def speed_limits_mode(self):
        return self._client.transfer_speed_limits_mode()
    speedLimitsMode = speed_limits_mode

    @speedLimitsMode.setter
    def speedLimitsMode(self, v):
        self.speed_limits_mode = v

    @speed_limits_mode.setter
    def speed_limits_mode(self, v):
        self.toggle_speed_limits_mode(intended_state=v)

    @Alias('toggleSpeedLimitsMode')
    def toggle_speed_limits_mode(self, intended_state=None, **kwargs):
        return self._client.transfer_toggle_speed_limits_mode(intended_state=intended_state, **kwargs)

    @property
    def download_limit(self):
        return self._client.transfer_download_limit()
    downloadLimit = download_limit

    @downloadLimit.setter
    def downloadLimit(self, v):
        self.download_limit = v

    @download_limit.setter
    def download_limit(self, v):
        self.set_download_limit(limit=v)

    @property
    def upload_limit(self):
        return self._client.transfer_upload_limit()
    uploadLimit = upload_limit

    @uploadLimit.setter
    def uploadLimit(self, v):
        self.upload_limit = v

    @upload_limit.setter
    def upload_limit(self, v):
        self.set_upload_limit(limit=v)

    @Alias('setDownloadLimit')
    def set_download_limit(self, limit=None, **kwargs):
        return self._client.transfer_set_download_limit(limit=limit, **kwargs)

    @Alias('setUploadLimit')
    def set_upload_limit(self, limit=None, **kwargs):
        return self._client.transfer_set_upload_limit(limit=limit, **kwargs)

    @Alias('banPeers')
    def ban_peers(self, peers=None, **kwargs):
        return self._client.transfer_ban_peers(peers=peers, **kwargs)


@aliased
class TransferAPIMixIn(Request):

    """Implementation of all Transfer API methods"""

    @property
    def transfer(self):
        """
       Allows for transparent interaction with Transfer endpoints.

       See Transfer class for usage.
       :return: Transfer object
       """
        if self._transfer is None:
            self._transfer = Transfer(client=self)
        return self._transfer

    @response_json(TransferInfoDictionary)
    @login_required
    def transfer_info(self, **kwargs):
        """
        Retrieves the global transfer info usually found in qBittorrent status bar.

        :return: dictionary of status items
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-global-transfer-info
        """
        return self._get(_name=APINames.Transfer, _method='info', **kwargs)

    @Alias('transfer_speedLimitsMode')
    @response_text(str)
    @login_required
    def transfer_speed_limits_mode(self, **kwargs):
        """
        Retrieves whether alternative speed limits are enabled. (alias: transfer_speedLimitMode)

        :return: '1' if alternative speed limits are currently enabled, '0' otherwise
        """
        return self._get(_name=APINames.Transfer, _method='speedLimitsMode', **kwargs)

    @Alias('transfer_toggleSpeedLimitsMode')
    @login_required
    def transfer_toggle_speed_limits_mode(self, intended_state=None, **kwargs):
        """
        Sets whether alternative speed limits are enabled. (alias: transfer_toggleSpeedLimitsMode)

        :param intended_state: True to enable alt speed and False to disable.
                               Leaving None will toggle the current state.
        :return: None
        """
        if (self.transfer_speed_limits_mode() == '1') is not intended_state or intended_state is None:
            self._post(_name=APINames.Transfer, _method='toggleSpeedLimitsMode', **kwargs)

    @Alias('transfer_downloadLimit')
    @response_text(int)
    @login_required
    def transfer_download_limit(self, **kwargs):
        """
        Retrieves download limit. 0 is unlimited. (alias: transfer_downloadLimit)

        :return: integer
        """
        return self._get(_name=APINames.Transfer, _method='downloadLimit', **kwargs)

    @Alias('transfer_uploadLimit')
    @response_text(int)
    @login_required
    def transfer_upload_limit(self, **kwargs):
        """
        Retrieves upload limit. 0 is unlimited. (alias: transfer_uploadLimit)

        :return: integer
        """
        return self._get(_name=APINames.Transfer, _method='uploadLimit', **kwargs)

    @Alias('transfer_setDownloadLimit')
    @login_required
    def transfer_set_download_limit(self, limit=None, **kwargs):
        """
        Set the global download limit in bytes/second. (alias: transfer_setDownloadLimit)

        :param limit: download limit in bytes/second (0 or -1 for no limit)
        :return: None
        """
        data = {'limit': limit}
        self._post(_name=APINames.Transfer, _method='setDownloadLimit', data=data, **kwargs)

    @Alias('transfer_setUploadLimit')
    @login_required
    def transfer_set_upload_limit(self, limit=None, **kwargs):
        """
        Set the global download limit in bytes/second. (alias: transfer_setUploadLimit)

        :param limit: upload limit in bytes/second (0 or -1 for no limit)
        :return: None
        """
        data = {'limit': limit}
        self._post(_name=APINames.Transfer, _method='setUploadLimit', data=data, **kwargs)

    @Alias('transfer_banPeers')
    @version_implemented('2.3', 'transfer/banPeers')
    @login_required
    def transfer_ban_peers(self, peers=None, **kwargs):
        """
        Ban one or more peers. (alias: transfer_banPeers)

        :param peers: one or more peers to ban. each peer should take the form 'host:port'
        :return: None
        """
        data = {'peers': self._list2string(peers, '|')}
        self._post(_name=APINames.Transfer, _method='banPeers', data=data, **kwargs)
