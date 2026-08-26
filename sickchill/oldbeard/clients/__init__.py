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


def getClientInstance(name):
    return __import__("sickchill.oldbeard.clients." + name.lower(), fromlist=_clients).Client


def getClientListDict(keys_only=False):
    if keys_only:
        return _clients + ["blackhole"]

    result = OrderedDict()
    result["blackhole"] = "Black Hole"
    for client in _clients:
        result[client] = _client_names.get(client, client)
    return result
