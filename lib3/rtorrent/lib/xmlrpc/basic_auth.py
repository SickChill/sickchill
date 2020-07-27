#
# Copyright (c) 2013 Dean Gardiner, <gardiner91@gmail.com>
#
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

import xmlrpc.client
from base64 import encodebytes


class BasicAuthTransport(xmlrpc.client.Transport):
    def __init__(self, username=None, password=None):
        xmlrpc.client.Transport.__init__(self)

        self.username = username
        self.password = password
        self.verbose = False

    def send_auth(self, h):
        if self.username is not None and self.password is not None:
            h.putheader('AUTHORIZATION', "Basic {}".format(encodebytes("{}:{}".format(self.username, self.password)).replace("\012", "")))

    def single_request(self, host, handler, request_body, verbose=0):
        # issue XML-RPC request
        try:
            connection = self.make_connection(host)
            headers = self._extra_headers[:]
            if verbose:
                connection.set_debuglevel(1)
            if self.accept_gzip_encoding :
                connection.putrequest("POST", handler, skip_accept_encoding=True)
                headers.append(("Accept-Encoding", "gzip"))
            else:
                connection.putrequest("POST", handler)
            headers.append(("Content-Type", "text/xml"))
            headers.append(("User-Agent", self.user_agent))
            self.send_headers(connection, headers)
            self.send_auth(connection)
            self.send_content(connection, request_body)

            response = connection.getresponse(buffering=True)
            if response.status == 200:
                self.verbose = verbose
                return self.parse_response(response)
        except xmlrpc.client.Fault:
            raise
        except Exception:
            self.close()
            raise

        #discard any response data and raise exception
        if response.getheader("content-length", 0):
            response.read()
        raise xmlrpc.client.ProtocolError(
            host + handler,
            response.status, response.reason,
            response.msg,
        )
