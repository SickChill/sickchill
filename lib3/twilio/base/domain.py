class Domain(object):
    """
    This represents at Twilio API subdomain.

    Like, `api.twilio.com` or `lookups.twilio.com'.
    """
    def __init__(self, twilio):
        """
        :param Twilio twilio:
        :return:
        """
        self.twilio = twilio
        self.base_url = None

    def absolute_url(self, uri):
        """
        Converts a relative `uri` to an absolute url.
        :param string uri: The relative uri to make absolute.
        :return: An absolute url (based off this domain)
        """
        return '{}/{}'.format(self.base_url.strip('/'), uri.strip('/'))

    def request(self, method, uri, params=None, data=None, headers=None,
                auth=None, timeout=None, allow_redirects=False):
        """
        Makes an HTTP request to this domain.
        :param string method: The HTTP method.
        :param string uri: The HTTP uri.
        :param dict params: Query parameters.
        :param object data: The request body.
        :param dict headers: The HTTP headers.
        :param tuple auth: Basic auth tuple of (username, password)
        :param int timeout: The request timeout.
        :param bool allow_redirects: True if the client should follow HTTP
        redirects.
        """
        url = self.absolute_url(uri)
        return self.twilio.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects
        )

