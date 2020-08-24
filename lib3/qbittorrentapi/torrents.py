import errno
from os import path
from os import strerror as os_strerror

try:
    from collections.abc import Iterable
    from collections.abc import Mapping
except ImportError:
    from collections import Iterable
    from collections import Mapping

import six
from attrdict import AttrDict

from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.definitions import List
from qbittorrentapi.definitions import ListEntry
from qbittorrentapi.definitions import TorrentStates
from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.decorators import response_text
from qbittorrentapi.decorators import version_implemented
from qbittorrentapi.exceptions import TorrentFileError
from qbittorrentapi.exceptions import TorrentFileNotFoundError
from qbittorrentapi.exceptions import TorrentFilePermissionError
from qbittorrentapi.request import Request


@aliased
class TorrentDictionary(Dictionary):
    """
    Alows interaction with individual torrents via the "Torrents" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'transfer_' prepended)
        >>> torrent = client.torrents.info()[0]
        >>> torrent_hash = torrent.info.hash
        >>> # Attributes without inputs and a return value are properties
        >>> properties = torrent.properties
        >>> trackers = torrent.trackers
        >>> files = torrent.files
        >>> # Action methods
        >>> torrent.edit_tracker(original_url="...", new_url="...")
        >>> torrent.remove_trackers(urls='http://127.0.0.2/')
        >>> torrent.rename(new_torrent_name="...")
        >>> torrent.resume()
        >>> torrent.pause()
        >>> torrent.recheck()
        >>> torrent.torrents_top_priority()
        >>> torrent.setLocation(location='/home/user/torrents/')
        >>> torrent.setCategory(category='video')
    """
    def __init__(self, data, client):
        self._torrent_hash = data.get('hash', None)
        super(TorrentDictionary, self).__init__(data=data, client=client)

    def sync_local(self):
        """Update local cache of torrent info."""
        for name, value in self.info.items():
            setattr(self, name, value)

    @property
    def state_enum(self):
        """Returns the formalized Enumeration for Torrent State instead of the raw string."""
        try:
            return TorrentStates(self.state)
        except ValueError:
            return TorrentStates.UNKNOWN

    @property
    def info(self):
        api_version = self._client._app_web_api_version_from_version_checker()
        if self._client._is_version_less_than(api_version, '2.0.1', lteq=False):
            info = [t for t in self._client.torrents_info() if t.hash == self._torrent_hash]
        else:
            info = self._client.torrents_info(torrent_hashes=self._torrent_hash)
        if len(info) == 1:
            return info[0]
        return AttrDict()

    def resume(self, **kwargs):
        self._client.torrents_resume(torrent_hashes=self._torrent_hash, **kwargs)

    def pause(self, **kwargs):
        self._client.torrents_pause(torrent_hashes=self._torrent_hash, **kwargs)

    def delete(self, delete_files=None, **kwargs):
        self._client.torrents_delete(delete_files=delete_files, torrent_hashes=self._torrent_hash, **kwargs)

    def recheck(self, **kwargs):
        self._client.torrents_recheck(torrent_hashes=self._torrent_hash, **kwargs)

    def reannounce(self, **kwargs):
        self._client.torrents_reannounce(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('increasePrio')
    def increase_priority(self, **kwargs):
        self._client.torrents_increase_priority(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('decreasePrio')
    def decrease_priority(self, **kwargs):
        self._client.torrents_decrease_priority(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('topPrio')
    def top_priority(self, **kwargs):
        self._client.torrents_top_priority(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('bottomPrio')
    def bottom_priority(self, **kwargs):
        self._client.torrents_bottom_priority(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setShareLimits')
    def set_share_limits(self, ratio_limit=None, seeding_time_limit=None, **kwargs):
        self._client.torrents_set_share_limits(ratio_limit=ratio_limit, seeding_time_limit=seeding_time_limit,
                                               torrent_hashes=self._torrent_hash, **kwargs)

    @property
    def download_limit(self, **kwargs):
        return self._client.torrents_download_limit(torrent_hashes=self._torrent_hash, **kwargs).get(self._torrent_hash)
    downloadLimit = download_limit

    @downloadLimit.setter
    def downloadLimit(self, v):
        self.download_limit = v

    @download_limit.setter
    def download_limit(self, v):
        self.set_download_limit(limit=v)

    @Alias('setDownloadLimit')
    def set_download_limit(self, limit=None, **kwargs):
        self._client.torrents_set_download_limit(limit=limit, torrent_hashes=self._torrent_hash, **kwargs)

    @property
    def upload_limit(self, **kwargs):
        return self._client.torrents_upload_limit(torrent_hashes=self._torrent_hash, **kwargs).get(self._torrent_hash)
    uploadLimit = upload_limit

    @uploadLimit.setter
    def uploadLimit(self, v):
        self.upload_limit = v

    @upload_limit.setter
    def upload_limit(self, v):
        self.set_upload_limit(limit=v)

    @Alias('setUploadLimit')
    def set_upload_limit(self, limit=None, **kwargs):
        self._client.torrents_set_upload_limit(limit=limit, torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setLocation')
    def set_location(self, location=None, **kwargs):
        self._client.torrents_set_location(location=location, torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setCategory')
    def set_category(self, category=None, **kwargs):
        self._client.torrents_set_category(category=category, torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setAutoManagement')
    def set_auto_management(self, enable=None, **kwargs):
        self._client.torrents_set_auto_management(enable=enable, torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('toggleSequentialDownload')
    def toggle_sequential_download(self, **kwargs):
        self._client.torrents_toggle_sequential_download(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('toggleFirstLastPiecePrio')
    def toggle_first_last_piece_priority(self, **kwargs):
        self._client.torrents_toggle_first_last_piece_priority(torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setForceStart')
    def set_force_start(self, enable=None, **kwargs):
        self._client.torrents_set_force_start(enable=enable, torrent_hashes=self._torrent_hash, **kwargs)

    @Alias('setSuperSeeding')
    def set_super_seeding(self, enable=None, **kwargs):
        self._client.torrents_set_super_seeding(enable=enable, torrent_hashes=self._torrent_hash, **kwargs)

    @property
    def properties(self):
        return self._client.torrents_properties(torrent_hash=self._torrent_hash)

    @property
    def trackers(self):
        return self._client.torrents_trackers(torrent_hash=self._torrent_hash)

    @trackers.setter
    def trackers(self, v):
        self.add_trackers(urls=v)

    @property
    def webseeds(self):
        return self._client.torrents_webseeds(torrent_hash=self._torrent_hash)

    @property
    def files(self):
        return self._client.torrents_files(torrent_hash=self._torrent_hash)

    @Alias('renameFile')
    def rename_file(self, file_id=None, new_file_name=None, **kwargs):
        self._client.torrents_rename_file(torrent_hash=self._torrent_hash, file_id=file_id, new_file_name=new_file_name, **kwargs)

    @property
    def piece_states(self):
        return self._client.torrents_piece_states(torrent_hash=self._torrent_hash)
    pieceStates = piece_states

    @property
    def piece_hashes(self):
        return self._client.torrents_piece_hashes(torrent_hash=self._torrent_hash)
    pieceHashes = piece_hashes

    @Alias('addTrackers')
    def add_trackers(self, urls=None, **kwargs):
        self._client.torrents_add_trackers(torrent_hash=self._torrent_hash, urls=urls, **kwargs)

    @Alias('editTracker')
    def edit_tracker(self, orig_url=None, new_url=None, **kwargs):
        self._client.torrents_edit_tracker(torrent_hash=self._torrent_hash, original_url=orig_url, new_url=new_url, **kwargs)

    @Alias('removeTrackers')
    def remove_trackers(self, urls=None, **kwargs):
        self._client.torrents_remove_trackers(torrent_hash=self._torrent_hash, urls=urls, **kwargs)

    @Alias('filePriority')
    def file_priority(self, file_ids=None, priority=None, **kwargs):
        self._client.torrents_file_priority(torrent_hash=self._torrent_hash, file_ids=file_ids, priority=priority, **kwargs)

    def rename(self, new_name=None, **kwargs):
        self._client.torrents_rename(torrent_hash=self._torrent_hash, new_torrent_name=new_name, **kwargs)

    @Alias('addTags')
    def add_tags(self, tags=None, **kwargs):
        self._client.torrents_add_tags(torrent_hashes=self._torrent_hash, tags=tags, **kwargs)

    @Alias('removeTags')
    def remove_tags(self, tags=None, **kwargs):
        self._client.torrents_remove_tags(torrent_hashes=self._torrent_hash, tags=tags, **kwargs)


class TorrentPropertiesDictionary(Dictionary):
    pass


class TorrentLimitsDictionary(Dictionary):
    pass


class TorrentCategoriesDictionary(Dictionary):
    pass


class TorrentsAddPeersDictionary(Dictionary):
    pass


class TorrentFilesList(List):
    def __init__(self, list_entries=None, client=None):
        super(TorrentFilesList, self).__init__(list_entries, entry_class=TorrentFile, client=client)
        for i, entry in enumerate(self):
            entry.update({'id': i})


class TorrentFile(ListEntry):
    pass


class WebSeedsList(List):
    def __init__(self, list_entries=None, client=None):
        super(WebSeedsList, self).__init__(list_entries, entry_class=WebSeed, client=client)


class WebSeed(ListEntry):
    pass


class TrackersList(List):
    def __init__(self, list_entries=None, client=None):
        super(TrackersList, self).__init__(list_entries, entry_class=Tracker, client=client)


class Tracker(ListEntry):
    pass


class TorrentInfoList(List):
    def __init__(self, list_entries=None, client=None):
        super(TorrentInfoList, self).__init__(list_entries, entry_class=TorrentDictionary, client=client)


class TorrentPieceInfoList(List):
    def __init__(self, list_entries=None, client=None):
        super(TorrentPieceInfoList, self).__init__(list_entries, entry_class=TorrentPieceData, client=client)


class TorrentPieceData(ListEntry):
    pass


class TagList(List):
    def __init__(self, list_entries=None, client=None):
        super(TagList, self).__init__(list_entries, entry_class=Tag, client=client)


class Tag(ListEntry):
    pass


class Torrents(ClientCache):
    """
    Allows interaction with the "Torrents" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'torrents_' prepended)
        >>> torrent_list = client.torrents.info()
        >>> torrent_list_active = client.torrents.info.active()
        >>> torrent_list_active_partial = client.torrents.info.active(limit=100, offset=200)
        >>> torrent_list_downloading = client.torrents.info.downloading()
        >>> # torrent looping
        >>> for torrent in client.torrents.info.completed()
        >>> # all torrents endpoints with a 'hashes' parameters support all method to apply action to all torrents
        >>> client.torrents.pause.all()
        >>> client.torrents.resume.all()
        >>> # or specify the individual hashes
        >>> client.torrents.downloadLimit(torrent_hashes=['...', '...'])
    """
    def __init__(self, client):
        super(Torrents, self).__init__(client=client)
        self.info = self._Info(client=client)
        self.resume = self._ActionForAllTorrents(client=client, func=client.torrents_resume)
        self.pause = self._ActionForAllTorrents(client=client, func=client.torrents_pause)
        self.delete = self._ActionForAllTorrents(client=client, func=client.torrents_delete)
        self.recheck = self._ActionForAllTorrents(client=client, func=client.torrents_recheck)
        self.reannounce = self._ActionForAllTorrents(client=client, func=client.torrents_reannounce)
        self.increase_priority = self._ActionForAllTorrents(client=client, func=client.torrents_increase_priority)
        self.increasePrio = self.increase_priority
        self.decrease_priority = self._ActionForAllTorrents(client=client, func=client.torrents_decrease_priority)
        self.decreasePrio = self.decrease_priority
        self.top_priority = self._ActionForAllTorrents(client=client, func=client.torrents_top_priority)
        self.topPrio = self.top_priority
        self.bottom_priority = self._ActionForAllTorrents(client=client, func=client.torrents_bottom_priority)
        self.bottomPrio = self.bottom_priority
        self.download_limit = self._ActionForAllTorrents(client=client, func=client.torrents_download_limit)
        self.downloadLimit = self.download_limit
        self.upload_limit = self._ActionForAllTorrents(client=client, func=client.torrents_upload_limit)
        self.uploadLimit = self.upload_limit
        self.set_download_limit = self._ActionForAllTorrents(client=client, func=client.torrents_set_download_limit)
        self.setDownloadLimit = self.set_download_limit
        self.set_share_limits = self._ActionForAllTorrents(client=client, func=client.torrents_set_share_limits)
        self.setShareLimits = self.set_share_limits
        self.set_upload_limit = self._ActionForAllTorrents(client=client, func=client.torrents_set_upload_limit)
        self.setUploadLimit = self.set_upload_limit
        self.set_location = self._ActionForAllTorrents(client=client, func=client.torrents_set_location)
        self.setLocation = self.set_location
        self.set_category = self._ActionForAllTorrents(client=client, func=client.torrents_set_category)
        self.setCategory = self.set_category
        self.set_auto_management = self._ActionForAllTorrents(client=client, func=client.torrents_set_auto_management)
        self.setAutoManagement = self.set_auto_management
        self.toggle_sequential_download = self._ActionForAllTorrents(client=client, func=client.torrents_toggle_sequential_download)
        self.toggleSequentialDownload = self.toggle_sequential_download
        self.toggle_first_last_piece_priority = self._ActionForAllTorrents(client=client, func=client.torrents_toggle_first_last_piece_priority)
        self.toggleFirstLastPiecePrio = self.toggle_first_last_piece_priority
        self.set_force_start = self._ActionForAllTorrents(client=client, func=client.torrents_set_force_start)
        self.setForceStart = self.set_force_start
        self.set_super_seeding = self._ActionForAllTorrents(client=client, func=client.torrents_set_super_seeding)
        self.setSuperSeeding = self.set_super_seeding
        self.add_peers = self._ActionForAllTorrents(client=client, func=client.torrents_add_peers)
        self.addPeers = self.add_peers

    def add(self, urls=None, torrent_files=None, save_path=None, cookie=None, category=None,
            is_skip_checking=None, is_paused=None, is_root_folder=None, rename=None,
            upload_limit=None, download_limit=None, use_auto_torrent_management=None,
            is_sequential_download=None, is_first_last_piece_priority=None, **kwargs):
        return self._client.torrents_add(urls=urls, torrent_files=torrent_files, save_path=save_path, cookie=cookie,
                                         category=category, is_skip_checking=is_skip_checking, is_paused=is_paused,
                                         is_root_folder=is_root_folder, rename=rename, upload_limit=upload_limit,
                                         download_limit=download_limit, is_sequential_download=is_sequential_download,
                                         use_auto_torrent_management=use_auto_torrent_management,
                                         is_first_last_piece_priority=is_first_last_piece_priority, **kwargs)

    class _ActionForAllTorrents(ClientCache):
        def __init__(self, client, func):
            super(Torrents._ActionForAllTorrents, self).__init__(client=client)
            self.func = func

        def __call__(self, torrent_hashes=None, **kwargs):
            return self.func(torrent_hashes=torrent_hashes, **kwargs)

        def all(self, **kwargs):
            return self.func(torrent_hashes='all', **kwargs)

    class _Info(ClientCache):
        def __call__(self, status_filter=None, category=None, sort=None, reverse=None, limit=None, offset=None,
                     torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter=status_filter, category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def all(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='all', category=category, sort=sort, reverse=reverse,
                                              limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def downloading(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='downloading', category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def completed(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='completed', category=category, sort=sort, reverse=reverse,
                                              limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def paused(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='paused', category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def active(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='active', category=category, sort=sort, reverse=reverse,
                                              limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def inactive(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='inactive', category=category, sort=sort, reverse=reverse,
                                              limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def resumed(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='resumed', category=category, sort=sort, reverse=reverse,
                                              limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def stalled(self, category=None, sort=None, reverse=None, limit=None, offset=None, torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='stalled', category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def stalled_uploading(self, category=None, sort=None, reverse=None, limit=None, offset=None,
                              torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='stalled_uploading', category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)

        def stalled_downloading(self, category=None, sort=None, reverse=None, limit=None, offset=None,
                                torrent_hashes=None, **kwargs):
            return self._client.torrents_info(status_filter='stalled_downloading', category=category, sort=sort,
                                              reverse=reverse, limit=limit, offset=offset, torrent_hashes=torrent_hashes, **kwargs)


@aliased
class TorrentCategories(ClientCache):
    """
    Alows interaction with torrent categories within the "Torrents" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this are all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'torrents_' prepended)
        >>> categories = client.torrent_categories.categories
        >>> # create or edit categories
        >>> client.torrent_categories.create_category(name='Video', save_path='/home/user/torrents/Video')
        >>> client.torrent_categories.edit_category(name='Video', save_path='/data/torrents/Video')
        >>> # edit or create new by assignment
        >>> client.torrent_categories.categories = dict(name='Video', save_path='/hone/user/')
        >>> # delete categories
        >>> client.torrent_categories.removeCategories(categories='Video')
        >>> client.torrent_categories.removeCategories(categories=['Audio', "ISOs"])
    """

    @property
    def categories(self):
        return self._client.torrents_categories()

    @categories.setter
    def categories(self, v):
        if v.get('name', '') in self.categories:
            self.edit_category(**v)
        else:
            self.create_category(**v)

    @Alias('createCategory')
    def create_category(self, name=None, save_path=None, **kwargs):
        return self._client.torrents_create_category(name=name, save_path=save_path, **kwargs)

    @Alias('editCategory')
    def edit_category(self, name=None, save_path=None, **kwargs):
        return self._client.torrents_edit_category(name=name, save_path=save_path, **kwargs)

    @Alias('removeCategories')
    def remove_categories(self, categories=None, **kwargs):
        return self._client.torrents_remove_categories(categories=categories, **kwargs)


@aliased
class TorrentTags(ClientCache):
    """
    Allows interaction with torrent tags within the "Torrent" API endpoints.

    Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> tags = client.torrent_tags.tags
        >>> client.torrent_tags.tags = 'tv show'  # create category
        >>> client.torrent_tags.create_tags(tags=['tv show', 'linux distro'])
        >>> client.torrent_tags.delete_tags(tags='tv show')
    """

    @property
    def tags(self):
        return self._client.torrents_tags()

    @tags.setter
    def tags(self, v):
        self._client.torrents_create_tags(tags=v)

    @Alias('addTags')
    def add_tags(self, tags=None, torrent_hashes=None, **kwargs):
        self._client.torrents_add_tags(tags=tags, torrent_hashes=torrent_hashes, **kwargs)

    @Alias('removeTags')
    def remove_tags(self, tags=None, torrent_hashes=None, **kwargs):
        self._client.torrents_remove_tags(tags=tags, torrent_hashes=torrent_hashes, **kwargs)

    @Alias('createTags')
    def create_tags(self, tags=None, **kwargs):
        self._client.torrents_create_tags(tags=tags, **kwargs)

    @Alias('deleteTags')
    def delete_tags(self, tags=None, **kwargs):
        self._client.torrents_delete_tags(tags=tags, **kwargs)


@aliased
class TorrentsAPIMixIn(Request):
    """Implementation of all Torrents API methods."""

    @property
    def torrents(self):
        """
        Allows for transparent interaction with Torrents endpoints.

        See Torrents and Torrent class for usage.
        :return: Torrents object
        """
        if self._torrents is None:
            self._torrents = Torrents(client=self)
        return self._torrents

    @property
    def torrent_categories(self):
        """
        Allows for transparent interaction with Torrent Categories endpoints.

        See Torrent_Categories class for usage.
        :return: Torrent Categories object
        """
        if self._torrent_categories is None:
            self._torrent_categories = TorrentCategories(client=self)
        return self._torrent_categories

    @property
    def torrent_tags(self):
        """
        Allows for transparent interaction with Torrent Tags endpoints.

        See Torrent_Tags class for usage.
        :return: Torrent Tags object
        """
        if self._torrent_tags is None:
            self._torrent_tags = TorrentTags(client=self)
        return self._torrent_tags

    @response_text(str)
    @login_required
    def torrents_add(self, urls=None, torrent_files=None, save_path=None, cookie=None, category=None,
                     is_skip_checking=None, is_paused=None, is_root_folder=None, rename=None,
                     upload_limit=None, download_limit=None, use_auto_torrent_management=None,
                     is_sequential_download=None, is_first_last_piece_priority=None, **kwargs):
        """
        Add one or more torrents by URLs and/or torrent files.

        :raises UnsupportedMediaType415Error: if file is not a valid torrent file
        :raises TorrentFileNotFoundError: if a torrent file doesn't exist
        :raises TorrentFilePermissionError: if read permission is denied to torrent file

        :param urls: single instance or an iterable of URLs (http://, https://, magnet: and bc://bt/)
        :param torrent_files: several options are available to send torrent files to qBittorrent:
                              1) single instance of bytes: useful if torrent file already read from disk or downloaded from internet.
                              2) single instance of file handle to torrent file: use open(<filepath>, 'rb') to open the torrent file.
                              3) single instance of a filepath to torrent file: e.g. '/home/user/torrent_filename.torrent'
                              4) an iterable of the single instances above to send more than one torrent file
                              5) dictionary with key/value pairs of torrent name and single instance of above object
                              Note: The torrent name in a dictionary is useful to identify which torrent file
                              errored. qBittorrent provides back that name in the error text. If a torrent
                              name is not provided, then the name of the file will be used. And in the case of
                              bytes (or if filename cannot be determined), the value 'torrent__n' will be used
        :param save_path: location to save the torrent data
        :param cookie: cookie to retrieve torrents by URL
        :param category: category to assign to torrent(s)
        :param is_skip_checking: skip hash checking
        :param is_paused: True to start torrent(s) paused
        :param is_root_folder: True or False to create root folder
        :param rename: new name for torrent(s)
        :param upload_limit: upload limit in bytes/second
        :param download_limit: download limit in bytes/second
        :param use_auto_torrent_management: True or False to use automatic torrent management
        :param is_sequential_download: True or False for sequential download
        :param is_first_last_piece_priority: True or False for first and last piece download priority
        :return: "Ok." for success and "Fails." for failure
        """

        data = {'urls': (None, self._list2string(urls, '\n')),
                'savepath': (None, save_path),
                'cookie': (None, cookie),
                'category': (None, category),
                'skip_checking': (None, is_skip_checking),
                'paused': (None, is_paused),
                'root_folder': (None, is_root_folder),
                'rename': (None, rename),
                'upLimit': (None, upload_limit),
                'dlLimit': (None, download_limit),
                'autoTMM': (None, use_auto_torrent_management),
                'sequentialDownload': (None, is_sequential_download),
                'firstLastPiecePrio': (None, is_first_last_piece_priority)}

        files = self._normalize_torrent_files(torrent_files)

        return self._post(_name=APINames.Torrents, _method='add', data=data, files=files, **kwargs)

    @staticmethod
    def _normalize_torrent_files(user_files):
        """
        Normalize the torrent file(s) from the user.
        The file(s) can be the raw bytes, file handle, filepath for a torrent file,
        or a Sequence (e.g. list|set|tuple) of any of these "files".
        Further, the file(s) can be in a dictionary with the "names" of the torrents as the keys.
        These "names" can be anything...but are mostly useful as identifiers for each file.
        """
        if not user_files:
            return None

        prefix = 'torrent__'
        # if it's string-like and not a list|set|tuple, then make it a list
        # checking for 'read' attr since a single file handle is iterable but also needs to be in a list
        if isinstance(user_files, six.string_types) or not isinstance(user_files, Iterable) or hasattr(user_files, 'read'):
            user_files = [user_files]

        # up convert to a dictionary to add fabricated torrent names
        norm_files = user_files if isinstance(user_files, Mapping) else {prefix + str(i): f for i, f in enumerate(user_files)}

        files = {}
        for name, torrent_file in norm_files.items():
            try:
                fh = None
                if isinstance(torrent_file, bytes):
                    # since strings are bytes on python 2, simple filepaths will end up here
                    # just check if it's a file first in that case...
                    # this does prevent providing more useful IO errors on python 2....but it's dead anyway...
                    try:
                        filepath = path.abspath(path.realpath(path.expanduser(str(torrent_file))))
                        if path.exists(filepath):
                            fh = open(filepath, 'rb')
                            name = path.basename(filepath)
                    except Exception:
                        fh = None
                    # if bytes, assume it's a raw torrent file that was downloaded or read from disk
                    if not fh:
                        fh = torrent_file
                elif hasattr(torrent_file, 'read') and callable(torrent_file.read):
                    # if hasattr('read'), assume this is a file handle from open() or similar...
                    #  there isn't a reliable way to detect a file-like object on both python 2 & 3
                    fh = torrent_file
                else:
                    # otherwise, coerce to a string and try to open it as a file
                    filepath = path.abspath(path.realpath(path.expanduser(str(torrent_file))))
                    fh = open(filepath, 'rb')
                    name = path.basename(filepath)

                # if using default name, let Requests try to figure out the filename to send
                # Requests will fall back to "name" as the dict key if fh doesn't provide a file name
                files[name] = fh if name.startswith(prefix) else (name, fh)
            except IOError as io_err:
                if io_err.errno == errno.ENOENT:
                    raise TorrentFileNotFoundError(errno.ENOENT, os_strerror(errno.ENOENT), torrent_file)
                elif io_err.errno == errno.EACCES:
                    raise TorrentFilePermissionError(errno.ENOENT, os_strerror(errno.EACCES), torrent_file)
                raise TorrentFileError(io_err)
        return files or None

    ##########################################################################
    # INDIVIDUAL TORRENT ENDPOINTS
    ##########################################################################
    @response_json(TorrentPropertiesDictionary)
    @login_required
    def torrents_properties(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's properties.

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: Dictionary of torrent properties
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-generic-properties
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='properties', data=data, **kwargs)

    @response_json(TrackersList)
    @login_required
    def torrents_trackers(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's trackers.

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: List of torrent's trackers
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-trackers
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='trackers', data=data, **kwargs)

    @response_json(WebSeedsList)
    @login_required
    def torrents_webseeds(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's web seeds.

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: List of torrent's web seeds
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-web-seeds
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='webseeds', data=data, **kwargs)

    @response_json(TorrentFilesList)
    @login_required
    def torrents_files(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's files.

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: List of torrent's files
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-contents
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='files', data=data, **kwargs)

    @Alias('torrents_pieceStates')
    @response_json(TorrentPieceInfoList)
    @login_required
    def torrents_piece_states(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's pieces' states. (alias: torrents_pieceStates)

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: list of torrent's pieces' states
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='pieceStates', data=data, **kwargs)

    @Alias('torrents_pieceHashes')
    @response_json(TorrentPieceInfoList)
    @login_required
    def torrents_piece_hashes(self, torrent_hash=None, **kwargs):
        """
        Retrieve individual torrent's pieces' hashes. (alias: torrents_pieceHashes)

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :return: List of torrent's pieces' hashes
        """
        data = {'hash': torrent_hash or kwargs.pop('hash')}
        return self._post(_name=APINames.Torrents, _method='pieceHashes', data=data, **kwargs)

    @Alias('torrents_addTrackers')
    @login_required
    def torrents_add_trackers(self, torrent_hash=None, urls=None, **kwargs):
        """
        Add trackers to a torrent. (alias: torrents_addTrackers)

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :param urls: tracker urls to add to torrent
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'urls': self._list2string(urls, '\n')}
        self._post(_name=APINames.Torrents, _method='addTrackers', data=data, **kwargs)

    @version_implemented('2.2.0', 'torrents/editTracker')
    @Alias('torrents_editTracker')
    @login_required
    def torrents_edit_tracker(self, torrent_hash=None, original_url=None, new_url=None, **kwargs):
        """
        Replace a torrent's tracker with a different one. (alias: torrents_editTrackers)

        :raises InvalidRequest400:
        :raises NotFound404Error:
        :raises Conflict409Error:

        :param torrent_hash: hash for torrent
        :param original_url: URL for existing tracker
        :param new_url: new URL to replace
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'origUrl': original_url,
                'newUrl': new_url}
        self._post(_name=APINames.Torrents, _method='editTracker', data=data, **kwargs)

    @version_implemented('2.2.0', 'torrents/removeTrackers')
    @Alias('torrents_removeTrackers')
    @login_required
    def torrents_remove_trackers(self, torrent_hash=None, urls=None, **kwargs):
        """
        Remove trackers from a torrent. (alias: torrents_removeTrackers)

        :raises NotFound404Error:
        :raises Conflict409Error:

        :param torrent_hash: hash for torrent
        :param urls: tracker urls to removed from torrent
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'urls': self._list2string(urls, '|')}
        self._post(_name=APINames.Torrents, _method='removeTrackers', data=data, **kwargs)

    @Alias('torrents_filePrio')
    @login_required
    def torrents_file_priority(self, torrent_hash=None, file_ids=None, priority=None, **kwargs):
        """
        Set priority for one or more files. (alias: torrents_filePrio)

        :raises InvalidRequest400: if priority is invalid or at least one file ID is not an integer
        :raises NotFound404Error:
        :raises Conflict409: if torrent metadata has not finished downloading or at least one file was not found
        :param torrent_hash: hash for torrent
        :param file_ids: single file ID or a list.
        :param priority: priority for file(s)
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#set-file-priority
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'id': self._list2string(file_ids, "|"),
                'priority': priority}
        self._post(_name=APINames.Torrents, _method='filePrio', data=data, **kwargs)

    @login_required
    def torrents_rename(self, torrent_hash=None, new_torrent_name=None, **kwargs):
        """
        Rename a torrent.

        :raises NotFound404Error:

        :param torrent_hash: hash for torrent
        :param new_torrent_name: new name for torrent
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'name': new_torrent_name}
        self._post(_name=APINames.Torrents, _method='rename', data=data, **kwargs)

    @version_implemented('2.4.0', 'torrents/renameFile')
    @Alias('torrents_renameFile')
    @login_required
    def torrents_rename_file(self, torrent_hash=None, file_id=None, new_file_name=None, **kwargs):
        """
        Rename a torrent file.

        :raises MissingRequiredParameters400Error:
        :raises NotFound404Error:
        :raises Conflict409Error:

        :param torrent_hash: hash for torrent
        :param file_id: id for file
        :param new_file_name: new name for file
        :return: None
        """
        data = {'hash': torrent_hash or kwargs.pop('hash'),
                'id': file_id,
                'name': new_file_name}
        self._post(_name=APINames.Torrents, _method='renameFile', data=data, **kwargs)

    ##########################################################################
    # MULTIPLE TORRENT ENDPOINTS
    ##########################################################################
    @response_json(TorrentInfoList)
    @version_implemented('2.0.1', 'torrents/info', ('torrent_hashes', 'hashes'))
    @login_required
    def torrents_info(self, status_filter=None, category=None, sort=None, reverse=None, limit=None, offset=None,
                      torrent_hashes=None, **kwargs):
        """
        Retrieves list of info for torrents.
        Note: hashes is available starting web API version 2.0.1

        :param status_filter: Filter list by all, downloading, completed, paused, active, inactive, resumed
                              stalled, stalled_uploading and stalled_downloading added in Web API v2.4.1
        :param category: Filter list by category
        :param sort: Sort list by any property returned
        :param reverse: Reverse sorting
        :param limit: Limit length of list
        :param offset: Start of list (if < 0, offset from end of list)
        :param torrent_hashes: Filter list by hash (separate multiple hashes with a '|')
        :return: List of torrents
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-torrent-list
        """
        data = {'filter': status_filter,
                'category': category,
                'sort': sort,
                'reverse': reverse,
                'limit': limit,
                'offset': offset,
                'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        return self._post(_name=APINames.Torrents, _method='info', data=data, **kwargs)

    @login_required
    def torrents_resume(self, torrent_hashes=None, **kwargs):
        """
        Resume one or more torrents in qBittorrent.

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='resume', data=data, **kwargs)

    @login_required
    def torrents_pause(self, torrent_hashes=None, **kwargs):
        """
        Pause one or more torrents in qBittorrent.

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), "|")}
        self._post(_name=APINames.Torrents, _method='pause', data=data, **kwargs)

    @login_required
    def torrents_delete(self, delete_files=None, torrent_hashes=None, **kwargs):
        """
        Remove a torrent from qBittorrent and optionally delete its files.

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param delete_files: True to delete the torrent's files
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'deleteFiles': delete_files}
        self._post(_name=APINames.Torrents, _method='delete', data=data, **kwargs)

    @login_required
    def torrents_recheck(self, torrent_hashes=None, **kwargs):
        """
        Recheck a torrent in qBittorrent.

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='recheck', data=data, **kwargs)

    @version_implemented('2.0.2', 'torrents/reannounce')
    @login_required
    def torrents_reannounce(self, torrent_hashes=None, **kwargs):
        """
        Reannounce a torrent.

        Note: torrents/reannounce not available web API version 2.0.2

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='reannounce', data=data, **kwargs)

    @Alias('torrents_increasePrio')
    @login_required
    def torrents_increase_priority(self, torrent_hashes=None, **kwargs):
        """
        Increase the priority of a torrent. Torrent Queuing must be enabled. (alias: torrents_increasePrio)

        :raises Conflict409:

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='increasePrio', data=data, **kwargs)

    @Alias('torrents_decreasePrio')
    @login_required
    def torrents_decrease_priority(self, torrent_hashes=None, **kwargs):
        """
        Decrease the priority of a torrent. Torrent Queuing must be enabled. (alias: torrents_decreasePrio)

        :raises Conflict409:

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='decreasePrio', data=data, **kwargs)

    @Alias('torrents_topPrio')
    @login_required
    def torrents_top_priority(self, torrent_hashes=None, **kwargs):
        """
        Set torrent as highest priority. Torrent Queuing must be enabled. (alias: torrents_topPrio)

        :raises Conflict409:

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='topPrio', data=data, **kwargs)

    @Alias('torrents_bottomPrio')
    @login_required
    def torrents_bottom_priority(self, torrent_hashes=None, **kwargs):
        """
        Set torrent as highest priority. Torrent Queuing must be enabled. (alias: torrents_bottomPrio)

        :raises Conflict409:

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='bottomPrio', data=data, **kwargs)

    @Alias('torrents_downloadLimit')
    @response_json(TorrentLimitsDictionary)
    @login_required
    def torrents_download_limit(self, torrent_hashes=None, **kwargs):
        """
        Retrieve the download limit for one or more torrents. (alias: torrents_downloadLimit)

        :return: dictioanry {hash: limit} (-1 represents no limit)
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        return self._post(_name=APINames.Torrents, _method='downloadLimit', data=data, **kwargs)

    @Alias('torrents_setDownloadLimit')
    @login_required
    def torrents_set_download_limit(self, limit=None, torrent_hashes=None, **kwargs):
        """
        Set the download limit for one or more torrents. (alias: torrents_setDownloadLimit)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param limit: bytes/second (-1 sets the limit to infinity)
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'limit': limit}
        self._post(_name=APINames.Torrents, _method='setDownloadLimit', data=data, **kwargs)

    @version_implemented('2.0.1', 'torrents/setShareLimits')
    @Alias('torrents_setShareLimits')
    @login_required
    def torrents_set_share_limits(self, ratio_limit=None, seeding_time_limit=None, torrent_hashes=None, **kwargs):
        """
        Set share limits for one or more torrents.

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param ratio_limit: max ratio to seed a torrent. (-2 means use the global value and -1 is no limit)
        :param seeding_time_limit: minutes (-2 means use the global value and -1 is no limit)
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'ratioLimit': ratio_limit,
                'seedingTimeLimit': seeding_time_limit}
        self._post(_name=APINames.Torrents, _method='setShareLimits', data=data, **kwargs)

    @Alias('torrents_uploadLimit')
    @response_json(TorrentLimitsDictionary)
    @login_required
    def torrents_upload_limit(self, torrent_hashes=None, **kwargs):
        """
        Retrieve the upload limit for one or more torrents. (alias: torrents_uploadLimit)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: dictionary of limits
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        return self._post(_name=APINames.Torrents, _method='uploadLimit', data=data, **kwargs)

    @Alias('torrents_setUploadLimit')
    @login_required
    def torrents_set_upload_limit(self, limit=None, torrent_hashes=None, **kwargs):
        """
        Set the upload limit for one or more torrents. (alias: torrents_setUploadLimit)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param limit: bytes/second (-1 sets the limit to infinity)
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'limit': limit}
        self._post(_name=APINames.Torrents, _method='setUploadLimit', data=data, **kwargs)

    @Alias('torrents_setLocation')
    @login_required
    def torrents_set_location(self, location=None, torrent_hashes=None, **kwargs):
        """
        Set location for torrents's files. (alias: torrents_setLocation)

        :raises Forbidden403Error: if the user doesn't have permissions to write to the location
        :raises Conflict409: if the directory cannot be created at the location

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param location: disk location to move torrent's files
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'location': location}
        self._post(_name=APINames.Torrents, _method='setLocation', data=data, **kwargs)

    @Alias('torrents_setCategory')
    @login_required
    def torrents_set_category(self, category=None, torrent_hashes=None, **kwargs):
        """
        Set a category for one or more torrents. (alias: torrents_setCategory)

        :raises Conflict409: for bad category

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param category: category to assign to torrent
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'category': category}
        self._post(_name=APINames.Torrents, _method='setCategory', data=data, **kwargs)

    @Alias('torrents_setAutoManagement')
    @login_required
    def torrents_set_auto_management(self, enable=None, torrent_hashes=None, **kwargs):
        """
        Enable or disable automatic torrent management for one or more torrents. (alias: torrents_setAutoManagement)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param enable: True or False
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'enable': enable}
        self._post(_name=APINames.Torrents, _method='setAutoManagement', data=data, **kwargs)

    @Alias('torrents_toggleSequentialDownload')
    @login_required
    def torrents_toggle_sequential_download(self, torrent_hashes=None, **kwargs):
        """
        Toggle sequential download for one or more torrents. (alias: torrents_toggleSequentialDownload)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'))}
        self._post(_name=APINames.Torrents, _method='toggleSequentialDownload', data=data, **kwargs)

    @Alias('torrents_toggleFirstLastPiecePrio')
    @login_required
    def torrents_toggle_first_last_piece_priority(self, torrent_hashes=None, **kwargs):
        """
        Toggle priority of first/last piece downloading. (alias: torrents_toggleFirstLastPiecePrio)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|')}
        self._post(_name=APINames.Torrents, _method='toggleFirstLastPiecePrio', data=data, **kwargs)

    @Alias('torrents_setForceStart')
    @login_required
    def torrents_set_force_start(self, enable=None, torrent_hashes=None, **kwargs):
        """
        Force start one or more torrents. (alias: torrents_setForceStart)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param enable: True or False (False makes this equivalent to torrents_resume())
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'value': enable}
        self._post(_name=APINames.Torrents, _method='setForceStart', data=data, **kwargs)

    @Alias('torrents_setSuperSeeding')
    @login_required
    def torrents_set_super_seeding(self, enable=None, torrent_hashes=None, **kwargs):
        """
        Set one or more torrents as super seeding. (alias: torrents_setSuperSeeding)

        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :param enable: True or False
        :return:
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'value': enable}
        self._post(_name=APINames.Torrents, _method='setSuperSeeding', data=data, **kwargs)

    @Alias('torrents_addPeers')
    @version_implemented('2.3.0', 'torrents/addPeers')
    @response_json(TorrentsAddPeersDictionary)
    @login_required
    def torrents_add_peers(self, peers=None, torrent_hashes=None, **kwargs):
        """
        Add one or more peers to one or more torrents. (alias: torrents_addPeers)

        :raises InvalidRequest400Error: for invalid peers

        :param peers: one or more peers to add. each peer should take the form 'host:port'
        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: dictionary - {<hash>: {'added': #, 'failed': #}}
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'peers': self._list2string(peers, '|')}
        return self._post(_name=APINames.Torrents, _method='addPeers', data=data, **kwargs)

    # TORRENT CATEGORIES ENDPOINTS
    @version_implemented('2.1.1', 'torrents/categories')
    @response_json(TorrentCategoriesDictionary)
    @login_required
    def torrents_categories(self, **kwargs):
        """
        Retrieve all category definitions

        Note: torrents/categories is not available until v2.1.0
        :return: dictionary of categories
        """
        return self._get(_name=APINames.Torrents, _method='categories', **kwargs)

    @Alias('torrents_createCategory')
    @version_implemented('2.1.0', 'torrents/createCategory', ('save_path', 'savePath'))
    @login_required
    def torrents_create_category(self, name=None, save_path=None, **kwargs):
        """
        Create a new torrent category. (alias: torrents_createCategory)

        Note: save_path is not available until web API version 2.1.0

        :raises Conflict409: if category name is not valid or unable to create

        :param name: name for new category
        :param save_path: location to save torrents for this category
        :return: None
        """
        data = {'category': name,
                'savePath': save_path}
        self._post(_name=APINames.Torrents, _method='createCategory', data=data, **kwargs)

    @version_implemented('2.1.0', 'torrents/editCategory')
    @Alias('torrents_editCategory')
    @login_required
    def torrents_edit_category(self, name=None, save_path=None, **kwargs):
        """
        Edit an existing category. (alias: torrents_editCategory)

        Note: torrents/editCategory not available until web API version 2.1.0

        :raises Conflict409:

        :param name: category to edit
        :param save_path: new location to save files for this category
        :return: None
        """
        data = {'category': name,
                'savePath': save_path}
        self._post(_name=APINames.Torrents, _method='editCategory', data=data, **kwargs)

    @Alias('torrents_removeCategories')
    @login_required
    def torrents_remove_categories(self, categories=None, **kwargs):
        """
        Delete one or more categories. (alias: torrents_removeCategories)

        :param categories: categories to delete
        :return: None
        """
        data = {'categories': self._list2string(categories, '\n')}
        self._post(_name=APINames.Torrents, _method='removeCategories', data=data, **kwargs)

    # TORRENT TAGS ENDPOINTS
    @version_implemented('2.3.0', 'torrents/tags')
    @response_json(TagList)
    @login_required
    def torrents_tags(self, **kwargs):
        """
        Retrieve all tag definitions.

        :return: list of tags
        """
        return self._get(_name=APINames.Torrents, _method='tags', **kwargs)

    @Alias('torrents_addTags')
    @version_implemented('2.3.0', 'torrents/addTags')
    @login_required
    def torrents_add_tags(self, tags=None, torrent_hashes=None, **kwargs):
        """
        Add one or more tags to one or more torrents. (alias: torrents_addTags)
        Note: Tags that do not exist will be created on-the-fly.

        :param tags: tag name or list of tags
        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'tags': self._list2string(tags, ',')}
        self._post(_name=APINames.Torrents, _method='addTags', data=data, **kwargs)

    @Alias('torrents_removeTags')
    @version_implemented('2.3.0', 'torrents/removeTags')
    @login_required
    def torrents_remove_tags(self, tags=None, torrent_hashes=None, **kwargs):
        """
        Add one or more tags to one or more torrents. (alias: torrents_removeTags)

        :param tags: tag name or list of tags
        :param torrent_hashes: single torrent hash or list of torrent hashes. Or 'all' for all torrents.
        :return: None
        """
        data = {'hashes': self._list2string(torrent_hashes or kwargs.get('hashes'), '|'),
                'tags': self._list2string(tags, ',')}
        self._post(_name=APINames.Torrents, _method='removeTags', data=data, **kwargs)

    @Alias('torrents_createTags')
    @version_implemented('2.3.0', 'torrents/createTags')
    @login_required
    def torrents_create_tags(self, tags=None, **kwargs):
        """
        Create one or more tags. (alias: torrents_createTags)

        :param tags: tag name or list of tags
        :return: None
        """
        data = {'tags': self._list2string(tags, ',')}
        self._post(_name=APINames.Torrents, _method='createTags', data=data, **kwargs)

    @Alias('torrents_deleteTags')
    @version_implemented('2.3.0', 'torrents/deleteTags')
    @login_required
    def torrents_delete_tags(self, tags=None, **kwargs):
        """
        Delete one or more tags. (alias: torrents_deleteTags)

        :param tags: tag name or list of tags
        :return: None
        """
        data = {'tags': self._list2string(tags, ',')}
        self._post(_name=APINames.Torrents, _method='deleteTags', data=data, **kwargs)
