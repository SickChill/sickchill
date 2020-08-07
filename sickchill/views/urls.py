import os

from tornado.web import RedirectHandler, StaticFileHandler, url

from sickchill import settings

from . import CalendarHandler, LoginHandler, LogoutHandler
from .api import ApiHandler, KeyHandler
from .routes import Route


class Urls(object):
    def __init__(self, **options):
        self.options = options
        self.urls = [
            url(r'{0}/favicon.ico'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(self.options['data_root'], 'images/ico/favicon.ico')}, name='favicon'),

            url(r'{0}/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(self.options['data_root'], 'images')}, name='images'),

            url(r'{0}/cache/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(settings.CACHE_DIR, 'images')}, name='image_cache'),

            url(r'{0}/css/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(self.options['data_root'], 'css')}, name='css'),

            url(r'{0}/js/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(self.options['data_root'], 'js')}, name='js'),

            url(r'{0}/fonts/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": os.path.join(self.options['data_root'], 'fonts')}, name='fonts'),

            # TODO: WTF is this?
            # url(r'{0}/videos/(.*)'.format(self.options['web_root']), StaticFileHandler,
            #     {"path": self.video_root}, name='videos'),

            url(r'{0}(/?.*)'.format(self.options['api_root']), ApiHandler, name='api'),
            url(r'{0}/getkey(/?.*)'.format(self.options['web_root']), KeyHandler, name='get_api_key'),

            url(r'{0}/api/builder'.format(self.options['web_root']), RedirectHandler, {"url": self.options['web_root'] + '/apibuilder/'},
                name='apibuilder'),
            url(r'{0}/login(/?)'.format(self.options['web_root']), LoginHandler, name='login'),
            url(r'{0}/logout(/?)'.format(self.options['web_root']), LogoutHandler, name='logout'),

            url(r'{0}/calendar/?'.format(self.options['web_root']), CalendarHandler, name='calendar')

            # routes added by @route decorator
            # Plus naked index with missing web_root prefix
        ] + Route.get_routes(self.options['web_root'])
        # + [r for r in Route.get_routes() if r.name == 'index']
