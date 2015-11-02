import inspect
import os
import tornado.web

route_list = []

class route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """gets called when we class decorate"""
        name = self.name and self.name or _handler.__name__
        self._routes.append((self._uri, _handler, name))
        return _handler

    @classmethod
    def get_routes(self, webroot=''):
        self._routes.reverse()
        routes = [tornado.web.url(webroot + _uri, _handler, name=name) for _uri, _handler, name, in self._routes]
        return routes

def route_redirect(from_, to, name=None):
    route._routes.append(tornado.web.url(from_, tornado.web.RedirectHandler, dict(url=to), name=name))