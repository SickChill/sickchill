class Response(object):
    def __init__(self, status_code, text, headers=None):
        self.content = text
        self.headers = headers
        self.cached = False
        self.status_code = status_code
        self.ok = self.status_code < 400

    @property
    def text(self):
        return self.content

    def __repr__(self):
        return 'HTTP {} {}'.format(self.status_code, self.content)
