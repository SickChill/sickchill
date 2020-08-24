from json import dumps

from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.decorators import version_implemented
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.request import Request


class RSSitemsDictionary(Dictionary):
    pass


class RSSRulesDictionary(Dictionary):
    pass


@aliased
class RSS(ClientCache):
    """
    Allows interaction with "RSS" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this is all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'log_' prepended)
        >>> rss_rules = client.rss.rules
        >>> client.rss.addFolder(folder_path="TPB")
        >>> client.rss.addFeed(url='...', item_path="TPB\\Top100")
        >>> client.rss.remove_item(item_path="TPB") # deletes TPB and Top100
        >>> client.rss.set_rule(rule_name="...", rule_def={...})
        >>> client.rss.items.with_data
        >>> client.rss.items.without_data
    """

    def __init__(self, client):
        super(RSS, self).__init__(client=client)
        self.items = RSS._Items(client=client)

    @Alias('addFolder')
    def add_folder(self, folder_path=None, **kwargs):
        return self._client.rss_add_folder(folder_path=folder_path, **kwargs)

    @Alias('addFeed')
    def add_feed(self, url=None, item_path=None, **kwargs):
        return self._client.rss_add_feed(url=url, item_path=item_path, **kwargs)

    @Alias('removeItem')
    def remove_item(self, item_path=None, **kwargs):
        return self._client.rss_remove_item(item_path=item_path, **kwargs)

    @Alias('moveItem')
    def move_item(self, orig_item_path=None, new_item_path=None, **kwargs):
        return self._client.rss_move_item(orig_item_path=orig_item_path, new_item_path=new_item_path, **kwargs)

    @Alias('refreshItem')
    def refresh_item(self, item_path=None):
        return self._client.rss_refresh_item(item_path=item_path)

    @Alias('markAsRead')
    def mark_as_read(self, item_path=None, article_id=None, **kwargs):
        return self._client.rss_mark_as_read(item_path=item_path, article_id=article_id, **kwargs)

    @Alias('setRule')
    def set_rule(self, rule_name=None, rule_def=None, **kwargs):
        return self._client.rss_set_rule(rule_name=rule_name, rule_def=rule_def, **kwargs)

    @Alias('renameRule')
    def rename_rule(self, orig_rule_name=None, new_rule_name=None, **kwargs):
        return self._client.rss_rename_rule(orig_rule_name=orig_rule_name, new_rule_name=new_rule_name, **kwargs)

    @Alias('removeRule')
    def remove_rule(self, rule_name=None, **kwargs):
        return self._client.rss_remove_rule(rule_name=rule_name, **kwargs)

    @property
    def rules(self):
        return self._client.rss_rules()

    @Alias('matchingArticles')
    def matching_articles(self, rule_name=None, **kwargs):
        return self._client.rss_matching_articles(rule_name=rule_name, **kwargs)

    class _Items(ClientCache):
        def __call__(self, include_feed_data=None, **kwargs):
            return self._client.rss_items(include_feed_data=include_feed_data, **kwargs)

        @property
        def without_data(self):
            return self._client.rss_items(include_feed_data=False)

        @property
        def with_data(self):
            return self._client.rss_items(include_feed_data=True)


@aliased
class RSSAPIMixIn(Request):
    """Implementation of all RSS API methods."""

    @property
    def rss(self):
        """
        Allows for transparent interaction with RSS endpoints.

        See RSS class for usage.
        :return: RSS object
        """
        if self._rss is None:
            self._rss = RSS(client=self)
        return self._rss

    @Alias('rss_addFolder')
    @login_required
    def rss_add_folder(self, folder_path=None, **kwargs):
        """
        Add a RSS folder. Any intermediate folders in path must already exist. (alias: rss_addFolder)

        :raises Conflict409Error:

        :param folder_path: path to new folder (e.g. Linux\ISOs)
        :return: None
        """
        data = {'path': folder_path}
        self._post(_name=APINames.RSS, _method='addFolder', data=data, **kwargs)

    @Alias('rss_addFeed')
    @login_required
    def rss_add_feed(self, url=None, item_path=None, **kwargs):
        """
        Add new RSS feed. Folders in path must already exist. (alias: rss_addFeed)

        :raises Conflict409Error:

        :param url: URL of RSS feed (e.g http://thepiratebay.org/rss/top100/200)
        :param item_path: Name and/or path for new feed (e.g. Folder\Subfolder\FeedName)
        :return: None
        """
        data = {'url': url,
                'path': item_path}
        self._post(_name=APINames.RSS, _method='addFeed', data=data, **kwargs)

    @Alias('rss_removeItem')
    @login_required
    def rss_remove_item(self, item_path=None, **kwargs):
        """
        Remove a RSS item (folder, feed, etc). (alias: rss_removeItem)

        NOTE: Removing a folder also removes everything in it.

        :raises Conflict409Error:

        :param item_path: path to item to be removed (e.g. Folder\Subfolder\ItemName)
        :return: None
        """
        data = {'path': item_path}
        self._post(_name=APINames.RSS, _method='removeItem', data=data, **kwargs)

    @Alias('rss_moveItem')
    @login_required
    def rss_move_item(self, orig_item_path=None, new_item_path=None, **kwargs):
        """
        Move/rename a RSS item (folder, feed, etc). (alias: rss_moveItem)

        :raises Conflict409Error:

        :param orig_item_path: path to item to be removed (e.g. Folder\Subfolder\ItemName)
        :param new_item_path: path to item to be removed (e.g. Folder\Subfolder\ItemName)
        :return: None
        """
        data = {'itemPath': orig_item_path,
                'destPath': new_item_path}
        self._post(_name=APINames.RSS, _method='moveItem', data=data, **kwargs)

    @response_json(RSSitemsDictionary)
    @login_required
    def rss_items(self, include_feed_data=None, **kwargs):
        """
        Retrieve RSS items and optionally feed data.

        :param include_feed_data: True or false to include feed data
        :return: dictionary of RSS items
        """
        params = {'withData': include_feed_data}
        return self._get(_name=APINames.RSS, _method='items', params=params, **kwargs)

    @version_implemented('2.2', 'rss/refreshItem')
    @Alias('rss_refreshItem')
    @login_required
    def rss_refresh_item(self, item_path=None, **kwargs):
        """
        Trigger a refresh for a RSS item (alias: rss_refreshItem)

        :param item_path: path to item to be refreshed (e.g. Folder\Subfolder\ItemName)
        :return: None
        """
        # HACK: v4.1.7 and v4.1.8 both use api v2.2; however, refreshItem was introduced in v4.1.8
        if self._is_version_less_than('v4.1.7', self.app_version(), False):
            data = {"itemPath": item_path}
            self._post(_name=APINames.RSS, _method='refreshItem', data=data, **kwargs)

    @version_implemented('2.5.1', 'rss/markAsRead')
    @Alias('rss_markAsRead')
    @login_required
    def rss_mark_as_read(self, item_path=None, article_id=None, **kwargs):
        """
        Mark RSS article as read. If article ID is not provider, the entire feed is marked as read. (alias: rss_markAsRead)

        :raises NotFound404Error:

        :param item_path: path to item to be refreshed (e.g. Folder\Subfolder\ItemName)
        :param article_id: article ID from rss_items()
        :return: None
        """
        data = {'itemPath': item_path,
                'articleId': article_id}
        self._post(_name=APINames.RSS, _method='markAsRead', data=data, **kwargs)

    @Alias('rss_setRule')
    @login_required
    def rss_set_rule(self, rule_name=None, rule_def=None, **kwargs):
        """
        Create a new RSS auto-downloading rule. (alias: rss_setRule)

        :param rule_name: name for new rule
        :param rule_def: dictionary with rule fields
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#set-auto-downloading-rule
        :return: None
        """
        data = {'ruleName': rule_name,
                'ruleDef': dumps(rule_def)}
        self._post(_name=APINames.RSS, _method='setRule', data=data, **kwargs)

    @Alias('rss_renameRule')
    @login_required
    def rss_rename_rule(self, orig_rule_name=None, new_rule_name=None, **kwargs):
        """
        Rename a RSS auto-download rule. (alias: rss_renameRule)

        :param orig_rule_name: current name of rule
        :param new_rule_name: new name for rule
        :return: None
        """
        data = {'ruleName': orig_rule_name,
                'newRuleName': new_rule_name}
        self._post(_name=APINames.RSS, _method='renameRule', data=data, **kwargs)

    @Alias('rss_removeRule')
    @login_required
    def rss_remove_rule(self, rule_name=None, **kwargs):
        """
        Delete a RSS auto-downloading rule. (alias: rss_removeRule)

        :param rule_name: Name of rule to delete
        :return: None
        """
        data = {'ruleName': rule_name}
        self._post(_name=APINames.RSS, _method='removeRule', data=data, **kwargs)

    @response_json(RSSRulesDictionary)
    @login_required
    def rss_rules(self, **kwargs):
        """
        Retrieve RSS auto-download rule definitions.

        :return: None
        """
        return self._get(_name=APINames.RSS, _method='rules', **kwargs)

    @version_implemented('2.5.1', 'rss/matchingArticles')
    @Alias('rss_matchingArticles')
    @response_json(RSSitemsDictionary)
    @login_required
    def rss_matching_articles(self, rule_name=None, **kwargs):
        """
        Fetch all articles matching a rule. (alias: rss_matchingArticles)

        :param rule_name: Name of rule to return matching articles
        :return: RSSitemsDictionary of articles
        """
        data = {'ruleName': rule_name}
        return self._post(_name=APINames.RSS, _method='matchingArticles', data=data, **kwargs)
