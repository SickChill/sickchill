import tornado.web


class Route(object):
    routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, handler):
        """ Gets called when we decorate a class """
        name = self.name or handler.__name__
        self.routes.append((self._uri, handler, name))
        return handler

    @classmethod
    def get_routes(cls, web_root=""):
        cls.routes.reverse()
        routes = [tornado.web.url(web_root + _uri, handler, name=name) for _uri, handler, name, in cls.routes]
        return routes


def route_redirect(src, dst, name=None):
    Route.routes.append(tornado.web.url(src, tornado.web.RedirectHandler, dict(url=dst), name=name))
