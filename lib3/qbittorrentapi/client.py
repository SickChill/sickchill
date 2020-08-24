from qbittorrentapi.app import AppAPIMixIn
from qbittorrentapi.log import LogAPIMixIn
from qbittorrentapi.sync import SyncAPIMixIn
from qbittorrentapi.transfer import TransferAPIMixIn
from qbittorrentapi.torrents import TorrentsAPIMixIn
from qbittorrentapi.rss import RSSAPIMixIn
from qbittorrentapi.search import SearchAPIMixIn

# NOTES
# Implementation
#     Required API parameters
#         - To avoid runtime errors, required API parameters are not explicitly
#           enforced in the code. Instead, I found if qBittorent returns HTTP400
#           without am error message, at least one required parameter is missing.
#           This raises a MissingRequiredParameters400 error.
#         - Alternatively, if a parameter is malformatted, HTTP400 is returned
#           with an error message.
#           This raises a InvalidRequest400 error.
#
#     Unauthorized HTTP 401
#         - This is only raised if XSS is detected or host header validation fails.
#
# API Peculiarities
#     app/setPreferences
#         - This was endlessly frustrating since it requires data in the
#           form of {'json': dumps({'dht': True})}...
#         - Sending an empty string for 'banned_ips' drops the useless message
#           below in to the log file (same for WebUI):
#             ' is not a valid IP address and was rejected while applying the list of banned addresses.'
#             - [Resolved] https://github.com/qbittorrent/qBittorrent/issues/10745
#
#     torrents/downloadLimit and uploadLimit
#         - Hashes handling is non-standard. 404 is not returned for bad hashes and 'all' doesn't work.
#         - https://github.com/qbittorrent/qBittorrent/blob/6de02b0f2a79eeb4d7fb624c39a9f65ffe181d68/src/webui/api/torrentscontroller.cpp#L754
#         - https://github.com/qbittorrent/qBittorrent/issues/10744
#
#     torrents/info
#         - when using a GET request, the params (such as category) seemingly can't
#           contain spaces; however, POST does work with spaces.
#         - [Resolved] https://github.com/qbittorrent/qBittorrent/issues/10606


class Client(AppAPIMixIn,
             LogAPIMixIn,
             SyncAPIMixIn,
             TransferAPIMixIn,
             TorrentsAPIMixIn,
             RSSAPIMixIn,
             SearchAPIMixIn):

    """
    Initialize API for qBittorrent client.

    Host must be specified. Username and password can be specified at login.
    A call to auth_log_in is not explicitly required if username and password are
    provided during Client construction.

    :param host: hostname for qBittorrent Web API (e.g. [http[s]://]localhost[:8080])
    :param port: port number for qBittorrent Web API (note: only used if host does not contain a port)
    :param username: user name for qBittorrent client
    :param password: password for qBittorrent client

    :param SIMPLE_RESPONSES: By default, complex objects are returned from some endpoints. These objects will allow for
        accessing responses' items as attributes and include methods for contextually relevant actions.
        This comes at the cost of performance. Generally, this cost isn't large; however, some
        endpoints, such as torrents_files() method, may need to convert a large payload.
        Set this to True to return the simple JSON back.
        Alternatively, set this to True only for an individual method call. For instance, when
        requesting the files for a torrent: client.torrents_files(hash='...', SIMPLE_RESPONSES=True).
    :param VERIFY_WEBUI_CERTIFICATE: Set to False to skip verify certificate for HTTPS connections;
        for instance, if the connection is using a self-signed certificate. Not setting this to False for self-signed
        certs will cause a APIConnectionError exception to be raised.
    :param RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS: Some Endpoints may not be implemented in older
        versions of qBittorrent. Setting this to True will raise a UnimplementedError instead of just returning None.
    :param DISABLE_LOGGING_DEBUG_OUTPUT: Turn off debug output from logging for this package as well as Requests & urllib3.
    """

    def __init__(self, host='', port=None, username=None, password=None, **kwargs):
        super(Client, self).__init__(host=host, port=port, username=username, password=password, **kwargs)
