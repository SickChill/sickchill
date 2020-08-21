import traceback

from tornado.web import RequestHandler

from sickchill import logger, settings
from sickchill.oldbeard import helpers


class KeyHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self):
        if self.get_query_argument('u', None) == settings.WEB_USERNAME and self.get_query_argument('p', None) == settings.WEB_PASSWORD:
            if not len(settings.API_KEY or ''):
                settings.API_KEY = helpers.generateApiKey()
            result = {'success': True, 'api_key': settings.API_KEY}
        else:
            result = {'success': False, 'error': _('Failed authentication while getting api key')}
            logger.warning(_(f'Authentication failed during api key request: {traceback.format_exc()}'))

        return self.finish(result)
