from collections import OrderedDict

_clients = sorted(["utorrent", "transmission", "deluge", "deluged", "download_station", "rtorrent", "qbittorrent", "mlnet", "putio"])

# Display names for the Search Settings dropdown — avoid Client() construction
# (qBittorrent.__init__ logs and builds an API client on every page render).
_client_names = {
    "utorrent": "uTorrent",
    "transmission": "Transmission",
    "deluge": "Deluge",
    "deluged": "DelugeD",
    "download_station": "DownloadStation",
    "rtorrent": "rTorrent",
    "qbittorrent": "qBittorrent",
    "mlnet": "mlnet",
    "putio": "put.io",
}

default_host = {
    "utorrent": "http://localhost:8000",
    "transmission": "http://localhost:9091",
    "deluge": "http://localhost:8112",
    "deluged": "scgi://localhost:58846",
    "download_station": "http://localhost:5000",
    "rtorrent": "scgi://localhost:5000",
    "qbittorrent": "http://localhost:8080",
    "mlnet": "http://localhost:4080",
    "putio": "https://api.put.io/login",
}


class _ClientPluginAdapter:
    """Thin facade: getClientInstance(name)() must keep working like legacy Client()."""

    def __init__(self, plugin_id, host=None, username=None, password=None):
        self.plugin_id = plugin_id
        self.host = host
        self.username = username
        self.password = password

    def _plugin(self):
        from sickchill.plugins.api import PluginKind
        from sickchill.plugins.manager import plugin_manager

        return plugin_manager.get(PluginKind.CLIENT, self.plugin_id)

    def _legacy_client(self):
        return __import__("sickchill.oldbeard.clients." + self.plugin_id, fromlist=_clients).Client(self.host, self.username, self.password)

    def sendTORRENT(self, result):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.send(result, host=self.host, username=self.username, password=self.password)
        return self._legacy_client().sendTORRENT(result)

    def send_nzb(self, result):
        plugin = self._plugin()
        if plugin is not None:
            if hasattr(plugin, "send_nzb"):
                return plugin.send_nzb(result, host=self.host, username=self.username, password=self.password)
            return plugin.send(result, host=self.host, username=self.username, password=self.password)
        client = self._legacy_client()
        return client.send_nzb(result)

    def test_client_connection(self):
        plugin = self._plugin()
        if plugin is not None:
            return plugin.test_client_connection(self.host, self.username, self.password)
        return self._legacy_client().test_client_connection()


def _adapter_factory(plugin_id):
    class Factory(_ClientPluginAdapter):
        def __init__(self, host=None, username=None, password=None):
            super().__init__(plugin_id, host=host, username=username, password=password)

    Factory.__name__ = f"{plugin_id}_Client"
    Factory.__qualname__ = Factory.__name__
    return Factory


def getClientInstance(name):
    name = (name or "").lower()
    try:
        from sickchill.plugins.api import PluginKind
        from sickchill.plugins.manager import plugin_manager

        if any(cls.id == name for cls in plugin_manager.classes(PluginKind.CLIENT)):
            return _adapter_factory(name)
    except Exception:
        pass

    if name == "blackhole":
        return _adapter_factory("blackhole")

    return __import__("sickchill.oldbeard.clients." + name, fromlist=_clients).Client


def getClientListDict(keys_only=False):
    if keys_only:
        return _clients + ["blackhole"]

    result = OrderedDict()
    result["blackhole"] = "Black Hole"
    for client in _clients:
        result[client] = _client_names.get(client, client)
    return result
