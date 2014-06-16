'''
Created on May 31, 2014

@author: Fenriswolf
'''
import logging
import inspect
import re
from collections import OrderedDict

from tornado.web import Application, RequestHandler, HTTPError

app_routing_log = logging.getLogger("tornado.application.routing")

class RoutingApplication(Application):
    def __init__(self, handlers=None, default_host="", transforms=None, wsgi=False, **settings):
        Application.__init__(self, handlers, default_host, transforms, wsgi, **settings)
        self.handler_map = OrderedDict()

    def expose(self, rule='', methods = ['GET'], kwargs=None, name=None):
        """
        A decorator that is used to register a given URL rule.
        """
        def decorator(func, *args, **kwargs):
            func_name = func.__name__
            frm = inspect.stack()[1]
            class_name = frm[3]
            module_name = frm[0].f_back.f_globals["__name__"]
            full_class_name = module_name + '.' + class_name

            for method in methods:
                func_rule = rule if rule else None
                if not func_rule:
                    if func_name == 'index':
                        func_rule = class_name
                    else:
                        func_rule = class_name + '/' + func_name
                    func_rule = r'/%s(.*)(/?)' % func_rule

                if full_class_name not in self.handler_map:
                    self.handler_map.setdefault(full_class_name, {})[method] = [(func_rule, func_name)]
                else:
                    self.handler_map[full_class_name][method] += [(func_rule, func_name)]

                app_routing_log.info("register %s %s to %s.%s" % (method, func_rule, full_class_name, func_name))

            return func
        return decorator

    def setRouteHandlers(self):
        handlers = [(rule[0], full_class_name)
                    for full_class_name, methods in self.handler_map.items()
                    for rules in methods.values()
                    for rule in rules]
        self.add_handlers(".*$", handlers)

class RequestRoutingHandler(RequestHandler):
    def _get_func_name(self):
        full_class_name = self.__module__ + '.' + self.__class__.__name__
        rules = self.application.handler_map.get(full_class_name, {}).get(self.request.method, [])

        for rule, func_name in rules:
            if not rule or not func_name:
                continue

            match = re.match(rule, self.request.path)
            if match:
                return func_name

        raise HTTPError(404, "")

    def _execute_method(self):
        if not self._finished:
            func_name = self._get_func_name()
            method = getattr(self, func_name)
            self._when_complete(method(*self.path_args, **self.path_kwargs),
                                self._execute_finish)