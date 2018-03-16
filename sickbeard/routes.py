""" Custom fast routes """
import tornado.web

route_list = []


class route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """ Gets called when we decorate a class """
        name = self.name and self.name or _handler.__name__
        self._routes.append((self._uri, _handler, name))
        return _handler

    @classmethod
    def get_routes(cls, webroot=''):
        cls._routes.reverse()
        routes = [tornado.web.url(webroot + _uri, _handler, name=name) for _uri, _handler, name, in cls._routes]
        return routes


def route_redirect(src, dst, name=None):
    route._routes.append(tornado.web.url(src, tornado.web.RedirectHandler, dict(url=dst), name=name))
