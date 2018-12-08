# Copyright (c) 2013 Chris Lucas, <chris@chrisjlucas.com>
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import urllib
import os.path
import time
import urllib
import xmlrpclib

import rtorrent.rpc
from rtorrent import common
from rtorrent.group import Group
from rtorrent.lib.torrentparser import TorrentParser
from rtorrent.lib.xmlrpc.http import HTTPServerProxy
from rtorrent.lib.xmlrpc.requests_transport import RequestsTransport
from rtorrent.lib.xmlrpc.scgi import SCGIServerProxy
from rtorrent.rpc import Method
from rtorrent.torrent import Torrent

__version__ = '0.2.9'
__author__ = 'Chris Lucas'
__contact__ = 'chris@chrisjlucas.com'
__license__ = 'MIT'

MIN_RTORRENT_VERSION = (0, 9, 0)
MIN_RTORRENT_VERSION_STR = common.convert_version_tuple_to_str(MIN_RTORRENT_VERSION)


class RTorrent:
    """Create a new rTorrent connection."""

    rpc_prefix = None

    def __init__(self, uri, username=None, password=None,
                 verify=False, sp=None, sp_kwargs=None, tp_kwargs=None):
        self.uri = uri  # : From X{__init__(self, url)}

        self.username = username
        self.password = password

        self.schema = urllib.splittype(uri)[0]

        if sp:
            self.sp = sp
        elif self.schema in ['http', 'https']:
            self.sp = HTTPServerProxy
            if self.schema == 'https':
                self.isHttps = True
            else:
                self.isHttps = False
        elif self.schema == 'scgi':
            self.sp = SCGIServerProxy
        else:
            raise NotImplementedError()

        self.sp_kwargs = sp_kwargs or {}

        self.tp_kwargs = tp_kwargs or {}

        self.torrents = []  # : List of L{Torrent} instances
        self._rpc_methods = []  # : List of rTorrent RPC methods
        self._torrent_cache = []
        self._client_version_tuple = ()

        if verify is True:
            self._verify_conn()

    def _get_conn(self):
        """Get ServerProxy instance."""
        if self.username is not None and self.password is not None:
            if self.schema == 'scgi':
                raise NotImplementedError()

            if 'authtype' not in self.tp_kwargs:
                authtype = None
            else:
                authtype = self.tp_kwargs['authtype']

            if 'check_ssl_cert' not in self.tp_kwargs:
                check_ssl_cert = True
            else:
                check_ssl_cert = self.tp_kwargs['check_ssl_cert']

            if 'proxies' not in self.tp_kwargs:
                proxies = None
            else:
                proxies = self.tp_kwargs['proxies']

            return self.sp(
                self.uri,
                transport=RequestsTransport(
                    use_https=self.isHttps,
                    authtype=authtype,
                    username=self.username,
                    password=self.password,
                    check_ssl_cert=check_ssl_cert,
                    proxies=proxies),
                **self.sp_kwargs
            )

        return self.sp(self.uri, **self.sp_kwargs)

    def _verify_conn(self):
        # check for rpc methods that should be available
        assert 'system.client_version' in self._get_rpc_methods(
        ), 'Required RPC method not available.'
        assert "system.library_version" in self._get_rpc_methods(
        ), 'Required RPC method not available.'

        # minimum rTorrent version check
        assert self._meets_version_requirement() is True,\
            'Error: Minimum rTorrent version required is {0}'.format(
            MIN_RTORRENT_VERSION_STR)

    def _meets_version_requirement(self):
        return self._get_client_version_tuple() >= MIN_RTORRENT_VERSION

    def _get_client_version_tuple(self):
        conn = self._get_conn()

        if not self._client_version_tuple:
            if not hasattr(self, 'client_version'):
                setattr(self, 'client_version',
                        conn.system.client_version())

            rtver = getattr(self, 'client_version')
            self._client_version_tuple = tuple([int(i) for i in
                                                rtver.split('.')])

        return self._client_version_tuple

    def _update_rpc_methods(self):
        self._rpc_methods = self._get_conn().system.listMethods()

        return self._rpc_methods

    def _get_rpc_methods(self):
        """Get list of raw RPC commands.

        @return: raw RPC commands
        @rtype: list
        """
        return(self._rpc_methods or self._update_rpc_methods())

    def get_torrents(self, view='main'):
        """Get list of all torrents in specified view.

        @return: list of L{Torrent} instances

        @rtype: list

        @todo: add validity check for specified view
        """
        self.torrents = []
        methods = rtorrent.torrent.methods
        retriever_methods = [m for m in methods
                             if m.is_retriever() and m.is_available(self)]

        m = rtorrent.rpc.Multicall(self)
        m.add('d.multicall2', '', view, 'd.hash=',
              *[method.rpc_call + '=' for method in retriever_methods])

        results = m.call()[0]  # only sent one call, only need first result

        for result in results:
            results_dict = {}
            # build results_dict
            # result[0] is the info_hash
            for m, r in zip(retriever_methods, result[1:]):
                results_dict[m.varname] = rtorrent.rpc.process_result(m, r)

            self.torrents.append(
                Torrent(self, info_hash=result[0], **results_dict)
            )

        self._manage_torrent_cache()
        return(self.torrents)

    def _manage_torrent_cache(self):
        """Carry tracker/peer/file lists over to new torrent list."""
        for torrent in self._torrent_cache:
            new_torrent = common.find_torrent(torrent.info_hash,
                                              self.torrents)
            if new_torrent is not None:
                new_torrent.files = torrent.files
                new_torrent.peers = torrent.peers
                new_torrent.trackers = torrent.trackers

        self._torrent_cache = self.torrents

    def _get_load_function(self, file_type, start, verbose):
        """Determine correct 'load torrent' RPC method."""
        func_name = None
        if file_type == 'url':
            # url strings can be input directly
            if start and verbose:
                func_name = 'load.start_verbose'
            elif start:
                func_name = 'load.start'
            elif verbose:
                func_name = 'load.verbose'
            else:
                func_name = 'load.normal'
        elif file_type in ['file', 'raw']:
            if start and verbose:
                func_name = 'load.raw_start_verbose'
            elif start:
                func_name = 'load.raw_start'
            elif verbose:
                func_name = 'load.raw_verbose'
            else:
                func_name = 'load.raw'

        return(func_name)

    def load_magnet(self, magneturl, info_hash, **kwargs):
        start = kwargs.pop('start', False)
        verbose = kwargs.pop('verbose', False)
        verify_load = kwargs.pop('verify_load', True)
        max_retries = kwargs.pop('max_retries', 5)
        params = kwargs.pop('params', [])
        target = kwargs.pop('target', '')

        p = self._get_conn()
        info_hash = info_hash.upper()

        func_name = self._get_load_function('url', start, verbose)

        getattr(p, func_name)(target, magneturl, *params)

        if verify_load:
            i = 0
            while i < max_retries:
                for torrent in self.get_torrents():
                    if torrent.info_hash == info_hash:
                        return True
                time.sleep(1)
                i += 1
            return False

        return True

    def load_torrent(self, torrent, **kwargs):
        """
        Load torrent into rTorrent (with various enhancements).

        @param torrent: can be a url, a path to a local file, or the raw data
        of a torrent file
        @type torrent: str

        @param start: start torrent when loaded
        @type start: bool

        @param verbose: print error messages to rTorrent log
        @type verbose: bool

        @param verify_load: verify that torrent was added to rTorrent successfully
        @type verify_load: bool

        @return: Depends on verify_load:
                 - if verify_load is True, (and the torrent was
                 loaded successfully), it'll return a L{Torrent} instance
                 - if verify_load is False, it'll return None

        @rtype: L{Torrent} instance or None

        @raise AssertionError: If the torrent wasn't successfully added to rTorrent
                               - Check L{TorrentParser} for the AssertionError's
                               it raises


        @note: Because this function includes url verification (if a url was input)
        as well as verification as to whether the torrent was successfully added,
        this function doesn't execute instantaneously. If that's what you're
        looking for, use load_torrent_simple() instead.
        """
        start = kwargs.pop('start', False)
        verbose = kwargs.pop('verbose', False)
        verify_load = kwargs.pop('verify_load', True)
        max_retries = kwargs.pop('max_retries', 5)
        params = kwargs.pop('params', [])
        target = kwargs.pop('target', '')

        p = self._get_conn()
        tp = TorrentParser(torrent)
        torrent = xmlrpclib.Binary(tp._raw_torrent)
        info_hash = tp.info_hash

        func_name = self._get_load_function('raw', start, verbose)

        getattr(p, func_name)(target, torrent, *params)

        if verify_load:
            i = 0
            while i < max_retries:
                for torrent in self.get_torrents():
                    if torrent.info_hash == info_hash:
                        return True
                time.sleep(1)
                i += 1
            return False

        return True

    def load_torrent_simple(self, torrent, file_type, **kwargs):
        """Load torrent into rTorrent.

        @param torrent: can be a url, a path to a local file, or the raw data
        of a torrent file
        @type torrent: str

        @param file_type: valid options: 'url', 'file', or 'raw'
        @type file_type: str

        @param start: start torrent when loaded
        @type start: bool

        @param verbose: print error messages to rTorrent log
        @type verbose: bool

        @return: None

        @raise AssertionError: if incorrect file_type is specified

        @note: This function was written for speed, it includes no enhancements.
        If you input a url, it won't check if it's valid. You also can't get
        verification that the torrent was successfully added to rTorrent.
        Use load_torrent() if you would like these features.
        """
        start = kwargs.pop('start', False)
        verbose = kwargs.pop('verbose', False)
        params = kwargs.pop('params', [])
        target = kwargs.pop('target', '')

        p = self._get_conn()

        if file_type not in ['raw', 'file', 'url']:
            print("Invalid file_type, options are: 'url', 'file', 'raw'.")
            return False

        func_name = self._get_load_function(file_type, start, verbose)

        if file_type == 'file':
            # since we have to assume we're connected to a remote rTorrent
            # client, we have to read the file and send it to rT as raw
            if not os.path.isfile(torrent):
                print('Invalid path: {0}'.format(torrent))
                return False

            torrent = open(torrent, 'rb').read()

        if file_type in ['raw', 'file']:
            finput = xmlrpclib.Binary(torrent)
        elif file_type == 'url':
            finput = torrent

        getattr(p, func_name)(target, finput, *params)

        return True

    def get_views(self):
        p = self._get_conn()
        return p.view_list()

    def create_group(self, name, persistent=True, view=None):
        p = self._get_conn()

        if persistent is True:
            p.group.insert_persistent_view('', name)
        elif view is not None:
            p.group.insert('', name, view)

        self._update_rpc_methods()

    def get_group(self, name):
        assert name is not None, 'group name required'

        group = Group(self, name)
        group.update()
        return group

    def set_dht_port(self, port):
        """Set DHT port.

        @param port: port
        @type port: int

        @raise AssertionError: if invalid port is given
        """
        assert common.is_valid_port(port), "Valid port range is 0-65535"
        self.dht_port = self._p.set_dht_port(port)

    def enable_check_hash(self):
        """Alias for set_check_hash(True)."""
        self.set_check_hash(True)

    def disable_check_hash(self):
        """Alias for set_check_hash(False)."""
        self.set_check_hash(False)

    def find_torrent(self, info_hash):
        """Frontend for rtorrent.common.find_torrent."""
        return(common.find_torrent(info_hash, self.get_torrents()))

    def poll(self):
        """Poll rTorrent to get latest torrent/peer/tracker/file information.

        @note: This essentially refreshes every aspect of the rTorrent
        connection, so it can be very slow if working with a remote
        connection that has a lot of torrents loaded.

        @return: None
        """
        self.update()
        torrents = self.get_torrents()
        for t in torrents:
            t.poll()

    def update(self):
        """Refresh rTorrent client info.

        @note: All fields are stored as attributes to self.

        @return: None
        """
        multicall = rtorrent.rpc.Multicall(self)
        retriever_methods = [m for m in methods
                             if m.is_retriever() and m.is_available(self)]
        for method in retriever_methods:
            multicall.add(method)

        multicall.call()


def _build_class_methods(class_obj):
    # multicall add class
    caller = lambda self, multicall, method, *args:\
        multicall.add(method, self.rpc_id, *args)

    caller.__doc__ = """Same as Multicall.add(), but with automatic inclusion
                        of the rpc_id

                        @param multicall: A L{Multicall} instance
                        @type: multicall: Multicall

                        @param method: L{Method} instance or raw rpc method
                        @type: Method or str

                        @param args: optional arguments to pass
                        """
    setattr(class_obj, 'multicall_add', caller)


def __compare_rpc_methods(rt_new, rt_old):
    from pprint import pprint
    rt_new_methods = set(rt_new._get_rpc_methods())
    rt_old_methods = set(rt_old._get_rpc_methods())
    print('New methods:')
    pprint(rt_new_methods - rt_old_methods)
    print('Methods not in new rTorrent:')
    pprint(rt_old_methods - rt_new_methods)


def __check_supported_methods(rt):
    from pprint import pprint
    supported_methods = set([m.rpc_call for m in
                             methods +
                             rtorrent.file.methods +
                             rtorrent.torrent.methods +
                             rtorrent.tracker.methods +
                             rtorrent.peer.methods])
    all_methods = set(rt._get_rpc_methods())

    print('Methods NOT in supported methods')
    pprint(all_methods - supported_methods)
    print('Supported methods NOT in all methods')
    pprint(supported_methods - all_methods)


methods = [
    # RETRIEVERS
    Method(RTorrent, 'get_xmlrpc_size_limit', 'network.xmlrpc.size_limit'),
    Method(RTorrent, 'get_proxy_address', 'network.proxy_address'),
    Method(RTorrent, 'get_file_split_suffix', 'system.file.split_suffix'),
    Method(RTorrent, 'get_global_up_limit', 'throttle.global_up.max_rate'),
    Method(RTorrent, 'get_max_memory_usage', 'pieces.memory.max'),
    Method(RTorrent, 'get_max_open_files', 'network.max_open_files'),
    Method(RTorrent, 'get_min_peers_seed', 'throttle.min_peers.seed'),
    Method(RTorrent, 'get_use_udp_trackers', 'trackers.use_udp'),
    Method(RTorrent, 'get_preload_min_size', 'pieces.preload.min_size'),
    Method(RTorrent, 'get_max_uploads', 'throttle.max_uploads'),
    Method(RTorrent, 'get_max_peers', 'throttle.max_peers.normal'),
    Method(RTorrent, 'get_timeout_sync', 'pieces.sync.timeout'),
    Method(RTorrent, 'get_receive_buffer_size', 'network.receive_buffer.size'),
    Method(RTorrent, 'get_split_file_size', 'system.file.split_size'),
    Method(RTorrent, 'get_dht_throttle', 'dht.throttle.name'),
    Method(RTorrent, 'get_max_peers_seed', 'throttle.max_peers.seed'),
    Method(RTorrent, 'get_min_peers', 'throttle.min_peers.normal'),
    Method(RTorrent, 'get_tracker_numwant', 'trackers.numwant'),
    Method(RTorrent, 'get_max_open_sockets', 'network.max_open_sockets'),
    Method(RTorrent, 'get_session_path', 'session.path'),
    Method(RTorrent, 'get_local_address', 'network.local_address'),
    Method(RTorrent, 'get_scgi_dont_route', 'network.scgi.dont_route'),
    Method(RTorrent, 'get_http_cacert', 'network.http.cacert'),
    Method(RTorrent, 'get_dht_port', 'dht.port'),
    Method(RTorrent, 'get_preload_type', 'pieces.preload.type'),
    Method(RTorrent, 'get_http_max_open', 'network.http.max_open'),
    Method(RTorrent, 'get_http_capath', 'network.http.capath'),
    Method(RTorrent, 'get_max_downloads_global', 'throttle.max_downloads.global'),
    Method(RTorrent, 'get_session_name', 'session.name'),
    Method(RTorrent, 'get_session_on_completion', 'session.on_completion'),
    Method(RTorrent, 'get_down_limit', 'throttle.global_down.max_rate'),
    Method(RTorrent, 'get_down_total', 'throttle.global_down.total'),
    Method(RTorrent, 'get_up_rate', 'throttle.global_up.rate'),
    Method(RTorrent, 'get_peer_exchange', 'protocol.pex'),
    Method(RTorrent, 'get_down_rate', 'throttle.global_down.rate'),
    Method(RTorrent, 'get_connection_seed', 'protocol.connection.seed'),
    Method(RTorrent, 'get_http_proxy_address', 'network.http.proxy_address'),
    Method(RTorrent, 'get_stats_preloaded', 'pieces.stats_preloaded'),
    Method(RTorrent, 'get_timeout_safe_sync', 'pieces.sync.timeout_safe'),
    Method(RTorrent, 'get_port_random', 'network.port_random'),
    Method(RTorrent, 'get_directory', 'directory.default'),
    Method(RTorrent, 'get_port_open', 'network.port_open'),
    Method(RTorrent, 'get_max_file_size', 'system.file.max_size'),
    Method(RTorrent, 'get_stats_not_preloaded', 'pieces.stats_not_preloaded'),
    Method(RTorrent, 'get_memory_usage', 'pieces.memory.current'),
    Method(RTorrent, 'get_connection_leech', 'protocol.connection.leech'),
    Method(RTorrent, 'get_hash_on_completion', 'pieces.hash.on_completion',
           boolean=True,
           ),
    Method(RTorrent, 'get_session_lock', 'session.use_lock'),
    Method(RTorrent, 'get_preload_min_rate', 'pieces.preload.min_rate'),
    Method(RTorrent, 'get_max_uploads_global', 'throttle.max_uploads.global'),
    Method(RTorrent, 'get_send_buffer_size', 'network.send_buffer.size'),
    Method(RTorrent, 'get_port_range', 'network.port_range'),
    Method(RTorrent, 'get_max_downloads_div', 'throttle.max_downloads.div'),
    Method(RTorrent, 'get_max_uploads_div', 'throttle.max_uploads.div'),
    Method(RTorrent, 'get_always_safe_sync', 'pieces.sync.always_safe'),
    Method(RTorrent, 'get_bind_address', 'network.bind_address'),
    Method(RTorrent, 'get_up_total', 'throttle.global_up.total'),
    Method(RTorrent, 'get_client_version', 'system.client_version'),
    Method(RTorrent, 'get_library_version', 'system.library_version'),
    Method(RTorrent, 'get_api_version', 'system.api_version',
           min_version=(0, 9, 1)
           ),
    Method(RTorrent, 'get_system_time', 'system.time',
           docstring="""Get the current time of the system rTorrent is running on

           @return: time (posix)
           @rtype: int""",
           ),

    # MODIFIERS
    Method(RTorrent, 'set_http_proxy_address', 'network.http.proxy_address.set'),
    Method(RTorrent, 'set_max_memory_usage', 'pieces.memory.max.set'),
    Method(RTorrent, 'set_max_file_size', 'system.file.max_size.set'),
    Method(RTorrent, 'set_bind_address', 'network.bind_address.set',
           docstring="""Set address bind

           @param arg: ip address
           @type arg: str
           """,
           ),
    Method(RTorrent, 'set_up_limit', 'throttle.global_up.max_rate.set',
           docstring="""Set global upload limit (in bytes)

           @param arg: speed limit
           @type arg: int
           """,
           ),
    Method(RTorrent, 'set_port_random', 'network.port_random.set'),
    Method(RTorrent, 'set_connection_leech', 'protocol.connection.leech.set'),
    Method(RTorrent, 'set_tracker_numwant', 'trackers.numwant.set'),
    Method(RTorrent, 'set_max_peers', 'throttle.max_peers.normal.set'),
    Method(RTorrent, 'set_min_peers', 'throttle.min_peers.normal.set'),
    Method(RTorrent, 'set_max_uploads_div', 'throttle.max_uploads.div.set'),
    Method(RTorrent, 'set_max_open_files', 'network.max_open_files.set'),
    Method(RTorrent, 'set_max_downloads_global', 'throttle.max_downloads.global.set'),
    Method(RTorrent, 'set_session_lock', 'session.use_lock.set'),
    Method(RTorrent, 'set_session_path', 'session.path.set'),
    Method(RTorrent, 'set_file_split_suffix', 'system.file.split_suffix.set'),
    Method(RTorrent, 'set_port_range', 'network.port_range.set'),
    Method(RTorrent, 'set_min_peers_seed', 'throttle.min_peers.seed.set'),
    Method(RTorrent, 'set_scgi_dont_route', 'network.scgi.dont_route.set'),
    Method(RTorrent, 'set_preload_min_size', 'pieces.preload.min_size.set'),
    Method(RTorrent, 'set_max_uploads_global', 'throttle.max_uploads.global.set'),
    Method(RTorrent, 'set_down_limit', 'throttle.global_down.max_rate.set',
           docstring="""Set global download limit (in bytes)

           @param arg: speed limit
           @type arg: int
           """,
           ),
    Method(RTorrent, 'set_preload_min_rate', 'pieces.preload.min_rate.set'),
    Method(RTorrent, 'set_max_peers_seed', 'throttle.max_peers.seed.set'),
    Method(RTorrent, 'set_max_uploads', 'throttle.max_uploads.set'),
    Method(RTorrent, 'set_session_on_completion', 'session.on_completion.set'),
    Method(RTorrent, 'set_max_open_http', 'network.http.max_open.set'),
    Method(RTorrent, 'set_directory', 'directory.default.set'),
    Method(RTorrent, 'set_http_cacert', 'network.http.cacert.set'),
    Method(RTorrent, 'set_dht_throttle', 'dht.throttle.name.set'),
    Method(RTorrent, 'set_proxy_address', 'network.proxy_address.set'),
    Method(RTorrent, 'set_split_file_size', 'system.file.split_size.set'),
    Method(RTorrent, 'set_receive_buffer_size', 'network.receive_buffer.size.set'),
    Method(RTorrent, 'set_use_udp_trackers', 'trackers.use_udp.set'),
    Method(RTorrent, 'set_connection_seed', 'protocol.connection.seed.set'),
    Method(RTorrent, 'set_xmlrpc_size_limit', 'network.xmlrpc.size_limit.set'),
    Method(RTorrent, 'set_xmlrpc_dialect', 'network.xmlrpc.dialect.set'),
    Method(RTorrent, 'set_always_safe_sync', 'pieces.sync.always_safe.set'),
    Method(RTorrent, 'set_http_capath', 'network.http.capath.set'),
    Method(RTorrent, 'set_send_buffer_size', 'network.send_buffer.size.set'),
    Method(RTorrent, 'set_max_downloads_div', 'throttle.max_downloads.div.set'),
    Method(RTorrent, 'set_session_name', 'session.name.set'),
    Method(RTorrent, 'set_port_open', 'network.port_open.set'),
    Method(RTorrent, 'set_timeout_sync', 'pieces.sync.timeout.set'),
    Method(RTorrent, 'set_peer_exchange', 'protocol.pex.set'),
    Method(RTorrent, 'set_local_address', 'network.local_address.set',
           docstring="""Set IP

           @param arg: ip address
           @type arg: str
           """,
           ),
    Method(RTorrent, 'set_timeout_safe_sync', 'pieces.sync.timeout_safe.set'),
    Method(RTorrent, 'set_preload_type', 'pieces.preload.type.set'),
    Method(RTorrent, 'set_hash_on_completion', 'pieces.hash.on_completion.set',
           docstring="""Enable/Disable hash checking on finished torrents

            @param arg: True to enable, False to disable
            @type arg: bool
            """,
           boolean=True,
           ),
]

_all_methods_list = [methods,
                     rtorrent.file.methods,
                     rtorrent.torrent.methods,
                     rtorrent.tracker.methods,
                     rtorrent.peer.methods,
                     ]

class_methods_pair = {
    RTorrent: methods,
    rtorrent.file.File: rtorrent.file.methods,
    rtorrent.torrent.Torrent: rtorrent.torrent.methods,
    rtorrent.tracker.Tracker: rtorrent.tracker.methods,
    rtorrent.peer.Peer: rtorrent.peer.methods,
}
for c in class_methods_pair.keys():
    rtorrent.rpc._build_rpc_methods(c, class_methods_pair[c])
    _build_class_methods(c)
