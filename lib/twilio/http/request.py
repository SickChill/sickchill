from twilio.compat import urlencode


class Request(object):
    """
    An HTTP request.
    """
    ANY = '*'

    def __init__(self,
                 method=ANY,
                 url=ANY,
                 auth=ANY,
                 params=ANY,
                 data=ANY,
                 headers=ANY,
                 **kwargs):
        self.method = method.upper()
        self.url = url
        self.auth = auth
        self.params = params
        self.data = data
        self.headers = headers

    @classmethod
    def attribute_equal(cls, lhs, rhs):
        if lhs == cls.ANY or rhs == cls.ANY:
            # ANY matches everything
            return True

        lhs = lhs or None
        rhs = rhs or None

        return lhs == rhs

    def __eq__(self, other):
        if not isinstance(other, Request):
            return False

        return self.attribute_equal(self.method, other.method) and \
            self.attribute_equal(self.url, other.url) and \
            self.attribute_equal(self.auth, other.auth) and \
            self.attribute_equal(self.params, other.params) and \
            self.attribute_equal(self.data, other.data) and \
            self.attribute_equal(self.headers, other.headers)

    def __str__(self):
        auth = ''
        if self.auth and self.auth != self.ANY:
            auth = '{} '.format(self.auth)

        params = ''
        if self.params and self.params != self.ANY:
            params = '?{}'.format(urlencode(self.params, doseq=True))

        data = ''
        if self.data and self.data != self.ANY:
            if self.method == 'GET':
                data = '\n -G'
            data += '\n{}'.format('\n'.join(' -d "{}={}"'.format(k, v) for k, v in self.data.items()))

        headers = ''
        if self.headers and self.headers != self.ANY:
            headers = '\n{}'.format('\n'.join(' -H "{}: {}"'.format(k, v)
                                              for k, v in self.headers.items()))

        return '{auth}{method} {url}{params}{data}{headers}'.format(
            auth=auth,
            method=self.method,
            url=self.url,
            params=params,
            data=data,
            headers=headers,
        )

    def __repr__(self):
        return str(self)
