# Copyright (c) 2013-2015 Alexandre Beloin, <alexandre.beloin@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""A transport for Python2/3 xmlrpc library using requests

Support:
-SSL with Basic and Digest authentication
-Proxies
"""

try:
    import xmlrpc.client as xmlrpc_client
except ImportError:
    import xmlrpclib as xmlrpc_client

import traceback

import requests
from requests.exceptions import RequestException
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3 import disable_warnings  # @UnresolvedImport


class RequestsTransport(xmlrpc_client.Transport):

    """Transport class for xmlrpc using requests"""

    def __init__(self, use_https=True, authtype=None, username=None,
                 password=None, check_ssl_cert=True, proxies=None):
        """Inits RequestsTransport.

        Args:
            use_https: If true, https else http
            authtype: None, basic or digest
            username: Username
            password: Password
            check_ssl_cert: Check SSL certificate
            proxies: A dict of proxies(
                     Ex: {"http": "http://10.10.1.10:3128",
                          "https": "http://10.10.1.10:1080",})

        Raises:
            ValueError: Invalid info
        """
        # Python 2 can't use super on old style class.
        if issubclass(xmlrpc_client.Transport, object):
            super(RequestsTransport, self).__init__()
        else:
            xmlrpc_client.Transport.__init__(self)

        self.user_agent = "Python Requests/" + requests.__version__

        self._use_https = use_https
        self._check_ssl_cert = check_ssl_cert

        if authtype == "basic" or authtype == "digest":
            self._authtype = authtype
        else:
            raise ValueError(
                "Supported authentication are: basic and digest")
        if authtype and (not username or not password):
            raise ValueError(
                "Username and password required when using authentication")

        self._username = username
        self._password = password
        if proxies is None:
            self._proxies = {}
        else:
            self._proxies = proxies

    def request(self, host, handler, request_body, verbose=0):
        """Replace the xmlrpc request function.

        Process xmlrpc request via requests library.

        Args:
            host: Target host
            handler: Target PRC handler.
            request_body: XML-RPC request body.
            verbose: Debugging flag.

        Returns:
            Parsed response.

        Raises:
            RequestException: Error in requests
        """
        if verbose:
            self._debug()

        if not self._check_ssl_cert:
            disable_warnings()

        headers = {'User-Agent': self.user_agent, 'Content-Type': 'text/xml', }

        # Need to be done because the schema(http or https) is lost in
        # xmlrpc.Transport's init.
        if self._use_https:
            url = "https://{host}/{handler}".format(host=host, handler=handler)
        else:
            url = "http://{host}/{handler}".format(host=host, handler=handler)

        # TODO Construct kwargs query instead
        try:
            if self._authtype == "basic":
                response = requests.post(
                    url,
                    data=request_body,
                    headers=headers,
                    verify=self._check_ssl_cert,
                    auth=HTTPBasicAuth(
                        self._username, self._password),
                    proxies=self._proxies)
            elif self._authtype == "digest":
                response = requests.post(
                    url,
                    data=request_body,
                    headers=headers,
                    verify=self._check_ssl_cert,
                    auth=HTTPDigestAuth(
                        self._username, self._password),
                    proxies=self._proxies)
            else:
                response = requests.post(
                    url,
                    data=request_body,
                    headers=headers,
                    verify=self._check_ssl_cert,
                    proxies=self._proxies)

            response.raise_for_status()
        except RequestException as error:
            raise xmlrpc_client.ProtocolError(url,
                                              error.message,
                                              traceback.format_exc(),
                                              response.headers)

        return self.parse_response(response)

    def parse_response(self, response):
        """Replace the xmlrpc parse_response function.

        Parse response.

        Args:
            response: Requests return data

        Returns:
            Response tuple and target method.
        """
        p, u = self.getparser()
        p.feed(response.text.encode('utf-8'))
        p.close()
        return u.close()

    def _debug(self):
        """Debug requests module.

        Enable verbose logging from requests
        """
        # TODO Ugly
        import logging
        try:
            import http.client as http_client
        except ImportError:
            import httplib as http_client

        http_client.HTTPConnection.debuglevel = 1

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
