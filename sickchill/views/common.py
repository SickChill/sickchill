import os
import re
import time

from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup
from mako.runtime import UNDEFINED
from mako.template import Template
from tornado.escape import linkify

from sickchill import settings
from sickchill.oldbeard import classes, helpers

mako_lookup = {}


def get_lookup():
    return mako_lookup.setdefault('mako', TemplateLookup(
        directories=[os.path.join(settings.PROG_DIR, "gui/" + settings.GUI_NAME + "/views/")],
        module_directory=os.path.join(settings.CACHE_DIR, 'mako'),
        strict_undefined=settings.BRANCH and settings.BRANCH != 'master',
        #  format_exceptions=True,
        filesystem_checks=True
    ))


class PageTemplate(Template):
    def __init__(self, rh, filename):
        super(PageTemplate, self).__init__(filename)
        self.context = {}

        lookup = get_lookup()
        self.template = lookup.get_template(filename)

        self.context['scRoot'] = settings.WEB_ROOT
        self.context['sbHttpPort'] = settings.WEB_PORT
        self.context['sbHttpsPort'] = settings.WEB_PORT
        self.context['sbHttpsEnabled'] = settings.ENABLE_HTTPS
        self.context['sbHandleReverseProxy'] = settings.HANDLE_REVERSE_PROXY
        self.context['sbDefaultPage'] = settings.DEFAULT_PAGE
        self.context['srLogin'] = rh.get_current_user()
        self.context['sbStartTime'] = rh.startTime
        self.context['static_url'] = rh.static_url
        self.context['reverse_url'] = rh.reverse_url
        self.context['linkify'] = linkify

        if rh.request.headers['Host'][0] == '[':
            self.context['sbHost'] = re.match(r"^\[.*\]", rh.request.headers['Host'], re.X | re.M | re.S).group(0)
        else:
            self.context['sbHost'] = re.match(r"^[^:]+", rh.request.headers['Host'], re.X | re.M | re.S).group(0)

        if "X-Forwarded-Host" in rh.request.headers:
            self.context['sbHost'] = rh.request.headers['X-Forwarded-Host']
        if "X-Forwarded-Port" in rh.request.headers:
            sbHttpPort = rh.request.headers['X-Forwarded-Port']
            self.context['sbHttpsPort'] = sbHttpPort
        if "X-Forwarded-Proto" in rh.request.headers:
            self.context['sbHttpsEnabled'] = rh.request.headers['X-Forwarded-Proto'].lower() == 'https'

        self.context['numErrors'] = len(classes.ErrorViewer.errors)
        self.context['numWarnings'] = len(classes.WarningViewer.errors)
        self.context['sbPID'] = str(settings.PID)

        self.context['title'] = "FixME"
        self.context['header'] = "FixME"
        self.context['topmenu'] = "FixME"
        self.context['submenu'] = []
        self.context['controller'] = "FixME"
        self.context['action'] = "FixME"
        self.context['show'] = UNDEFINED
        self.context['manage_torrents_url'] = helpers.manage_torrents_url()
        self.context['get_current_user'] = rh.get_current_user
        self.context['remote_ip'] = rh.request.remote_ip

    def render(self, *args, **kwargs):
        self.context['makoStartTime'] = time.time()
        context = self.context
        context.update(kwargs)
        # noinspection PyBroadException
        try:
            return self.template.render_unicode(*args, **context)
        except Exception as error:
            print(error)
            context['title'] = '500'
            context['header'] = _('Mako Error')
            context['backtrace'] = RichTraceback()
            return get_lookup().get_template('500.mako').render_unicode(*args, **context)
