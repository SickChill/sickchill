




# Stdlib Imports
import traceback

# Third Party Imports
from tornado.web import RequestHandler

# First Party Imports
from sickchill import settings
from sickchill.sickbeard import helpers, logger


class KeyHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super(KeyHandler, self).__init__(*args, **kwargs)

    def get(self):
        if self.get_query_argument('u', None) == settings.WEB_USERNAME and self.get_query_argument('p', None) == settings.WEB_PASSWORD:
            if not len(settings.API_KEY or ''):
                settings.API_KEY = helpers.generateApiKey()
            result = {'success': True, 'api_key': settings.API_KEY}
        else:
            result = {'success': False, 'error': _('Failed authentication while getting api key')}
            logger.warning(_('Authentication failed during api key request: {0}').format((traceback.format_exc())))

        return self.finish(result)
