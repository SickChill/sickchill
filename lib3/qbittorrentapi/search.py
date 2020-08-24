from qbittorrentapi.decorators import Alias
from qbittorrentapi.decorators import aliased
from qbittorrentapi.decorators import login_required
from qbittorrentapi.decorators import response_json
from qbittorrentapi.decorators import version_implemented
from qbittorrentapi.definitions import APINames
from qbittorrentapi.definitions import ClientCache
from qbittorrentapi.definitions import Dictionary
from qbittorrentapi.definitions import List
from qbittorrentapi.definitions import ListEntry
from qbittorrentapi.request import Request


class SearchJobDictionary(Dictionary):
    def __init__(self, data, client):
        self._search_job_id = data.get('id', None)
        super(SearchJobDictionary, self).__init__(data=data, client=client)

    def stop(self, **kwargs):
        return self._client.search.stop(search_id=self._search_job_id, **kwargs)

    def status(self, **kwargs):
        return self._client.search.status(search_id=self._search_job_id, **kwargs)

    def results(self, limit=None, offset=None, **kwargs):
        return self._client.search.results(limit=limit, offset=offset, search_id=self._search_job_id, **kwargs)

    def delete(self, **kwargs):
        return self._client.search.delete(search_id=self._search_job_id, **kwargs)


class SearchResultsDictionary(Dictionary):
    pass


class SearchStatusesList(List):
    def __init__(self, list_entries=None, client=None):
        super(SearchStatusesList, self).__init__(list_entries, entry_class=SearchStatus, client=client)


class SearchStatus(ListEntry):
    pass


class SearchCategoriesList(List):
    def __init__(self, list_entries=None, client=None):
        super(SearchCategoriesList, self).__init__(list_entries, entry_class=SearchCategory, client=client)


class SearchCategory(ListEntry):
    pass


class SearchPluginsList(List):
    def __init__(self, list_entries=None, client=None):
        super(SearchPluginsList, self).__init__(list_entries, entry_class=SearchPlugin, client=client)


class SearchPlugin(ListEntry):
    pass


@aliased
class Search(ClientCache):
    """
    Allows interaction with "Search" API endpoints.

    :Usage:
        >>> from qbittorrentapi import Client
        >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
        >>> # this is all the same attributes that are available as named in the
        >>> #  endpoints or the more pythonic names in Client (with or without 'search_' prepended)
        >>> # initiate searches and retrieve results
        >>> search_job = client.search.start(pattern='Ubuntu', plugins='all', category='all')
        >>> status = search_job.status()
        >>> results = search_job.result()
        >>> search_job.delete()
        >>> # inspect and manage plugins
        >>> plugins = client.search.plugins
        >>> cats = client.search.categories(plugin_name='...')
        >>> client.search.install_plugin(sources='...')
        >>> client.search.update_plugins()
    """

    def start(self, pattern=None, plugins=None, category=None, **kwargs):
        return self._client.search_start(pattern=pattern, plugins=plugins, category=category, **kwargs)

    def stop(self, search_id=None, **kwargs):
        return self._client.search_stop(search_id=search_id, **kwargs)

    def status(self, search_id=None, **kwargs):
        return self._client.search_status(search_id=search_id, **kwargs)

    def results(self, search_id=None, limit=None, offset=None, **kwargs):
        return self._client.search_results(search_id=search_id, limit=limit, offset=offset, **kwargs)

    def delete(self, search_id=None, **kwargs):
        return self._client.search_delete(search_id=search_id, **kwargs)

    def categories(self, plugin_name=None, **kwargs):
        return self._client.search_categories(plugin_name=plugin_name, **kwargs)

    @property
    def plugins(self):
        return self._client.search_plugins()

    @Alias('installPlugin')
    def install_plugin(self, sources=None, **kwargs):
        return self._client.search_install_plugin(sources=sources, **kwargs)

    @Alias('uninstallPlugin')
    def uninstall_plugin(self, sources=None, **kwargs):
        return self._client.search_uninstall_plugin(sources=sources, **kwargs)

    @Alias('enablePlugin')
    def enable_plugin(self, plugins=None, enable=None, **kwargs):
        return self._client.search_enable_plugin(plugins=plugins, enable=enable, **kwargs)

    @Alias('updatePlugins')
    def update_plugins(self, **kwargs):
        return self._client.search_update_plugins(**kwargs)


@aliased
class SearchAPIMixIn(Request):
    """Implementation for all Search API methods."""

    @property
    def search(self):
        """
        Allows for transparent interaction with Search endpoints.

        See Search class for usage.
        :return: Search object
        """
        if self._search is None:
            self._search = Search(client=self)
        return self._search

    @version_implemented('2.1.1', 'search/start')
    @response_json(SearchJobDictionary)
    @login_required
    def search_start(self, pattern=None, plugins=None, category=None, **kwargs):
        """
        Start a search. Python must be installed. Host may limit number of concurrent searches.

        :raises Conflict409Error:

        :param pattern: term to search for
        :param plugins: list of plugins to use for searching (supports 'all' and 'enabled')
        :param category: categories to limit search; dependent on plugins. (supports 'all')
        :return: search job
        """
        data = {'pattern': pattern,
                'plugins': self._list2string(plugins, '|'),
                'category': category}
        return self._post(_name=APINames.Search, _method='start', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/stop')
    @login_required
    def search_stop(self, search_id=None, **kwargs):
        """
        Stop a running search.

        :raises NotFound404Error:

        :param search_id: ID of search job to stop
        :return: None
        """
        data = {'id': search_id}
        self._post(_name=APINames.Search, _method='stop', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/status')
    @response_json(SearchStatusesList)
    @login_required
    def search_status(self, search_id=None, **kwargs):
        """
        Retrieve status of one or all searches.

        :raises NotFound404Error:

        :param search_id: ID of search to get status; leave emtpy for status of all jobs
        :return: dictionary of searches
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-search-status
        """
        params = {'id': search_id}
        return self._get(_name=APINames.Search, _method='status', params=params, **kwargs)

    @version_implemented('2.1.1', 'search/results')
    @response_json(SearchResultsDictionary)
    @login_required
    def search_results(self, search_id=None, limit=None, offset=None, **kwargs):
        """
        Retrieve the results for the search.

        :raises NotFound404Error:
        :raises Conflict409Error:

        :param search_id: ID of search job
        :param limit: number of results to return
        :param offset: where to start returning results
        :return: Dictionary of results
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-search-results
        """
        data = {'id': search_id,
                'limit': limit,
                'offset': offset}
        return self._post(_name=APINames.Search, _method='results', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/delete')
    @login_required
    def search_delete(self, search_id=None, **kwargs):
        """
        Delete a search job.

        :raises NotFound404Error:

        :param search_id: ID of search to delete
        :return: None
        """
        data = {'id': search_id}
        self._post(_name=APINames.Search, _method='delete', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/categories')
    @response_json(SearchCategoriesList)
    @login_required
    def search_categories(self, plugin_name=None, **kwargs):
        """
        Retrieve categories for search.

        :param plugin_name: Limit categories returned by plugin(s) (supports 'all' and 'enabled')
        :return: list of categories
        """
        data = {'pluginName': plugin_name}
        return self._post(_name=APINames.Search, _method='categories', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/plugins')
    @response_json(SearchPluginsList)
    @login_required
    def search_plugins(self, **kwargs):
        """
        Retrieve details of search plugins.

        :return: List of plugins.
            Properties: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)#get-search-plugins
        """
        return self._get(_name=APINames.Search, _method='plugins', **kwargs)

    @version_implemented('2.1.1', 'search/installPlugin')
    @Alias('search_installPlugin')
    @login_required
    def search_install_plugin(self, sources=None, **kwargs):
        """
        Install search plugins from either URL or file. (alias: search_installPlugin)

        :param sources: list of URLs or filepaths
        :return: None
        """
        data = {'sources': self._list2string(sources, '|')}
        self._post(_name=APINames.Search, _method='installPlugin', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/uninstallPlugin')
    @Alias('search_uninstallPlugin')
    @login_required
    def search_uninstall_plugin(self, names=None, **kwargs):
        """
        Uninstall search plugins. (alias: search_uninstallPlugin)

        :param names: names of plugins to uninstall
        :return: None
        """
        data = {'names': self._list2string(names, '|')}
        self._post(_name=APINames.Search, _method='uninstallPlugin', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/enablePlugin')
    @Alias('search_enablePlugin')
    @login_required
    def search_enable_plugin(self, plugins=None, enable=None, **kwargs):
        """
        Enable or disable search plugin(s). (alias: search_enablePlugin)

        :param plugins: list of plugin names
        :param enable: True or False
        :return: None
        """
        data = {'names': self._list2string(plugins, '|'),
                'enable': enable}
        self._post(_name=APINames.Search, _method='enablePlugin', data=data, **kwargs)

    @version_implemented('2.1.1', 'search/updatePlugin')
    @Alias('search_updatePlugins')
    @login_required
    def search_update_plugins(self, **kwargs):
        """
        Auto update search plugins. (alias: search_updatePlugins)

        :return: None
        """
        self._post(_name=APINames.Search, _method='updatePlugins', **kwargs)
