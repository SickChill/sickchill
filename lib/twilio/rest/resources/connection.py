from .imports import (
    httplib2,
    socks,
    PROXY_TYPE_HTTP,
    PROXY_TYPE_SOCKS4,
    PROXY_TYPE_SOCKS5
)


class Connection(object):
    '''Class for setting proxy configuration to be used for REST calls.'''
    _proxy_info = None

    @classmethod
    def proxy_info(cls):
        '''Returns the currently-set proxy information
        as an httplib2.ProxyInfo object.
        '''
        return cls._proxy_info

    @classmethod
    def set_proxy_info(cls, proxy_host, proxy_port,
                       proxy_type=PROXY_TYPE_HTTP, proxy_rdns=None,
                       proxy_user=None, proxy_pass=None):
        '''Set proxy configuration for future REST API calls.

        :param str proxy_host: Hostname of the proxy to use.
        :param int proxy_port: Port to connect to.
        :param proxy_type: The proxy protocol to use. One of
        PROXY_TYPE_HTTP, PROXY_TYPE_SOCKS4, PROXY_TYPE_SOCKS5.
        Defaults to connection.PROXY_TYPE_HTTP.
        :param bool proxy_rdns: Use the proxy host's DNS resolver.
        :param str proxy_user: Username for the proxy.
        :param str proxy_pass: Password for the proxy.
        '''

        cls._proxy_info = httplib2.ProxyInfo(
            proxy_type,
            proxy_host,
            proxy_port,
            proxy_rdns=proxy_rdns,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
        )


_hush_pyflakes = [
    socks,
    PROXY_TYPE_SOCKS4,
    PROXY_TYPE_SOCKS5
]
