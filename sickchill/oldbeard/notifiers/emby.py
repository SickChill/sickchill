import requests

from sickchill import logger, settings


class Notifier(object):

    def __init__(self):
        self.session = None

    def __make_session(self, emby_apikey=None):
        if self.session:
            return self.session

        if not emby_apikey:
            emby_apikey = settings.EMBY_APIKEY

        self.session = requests.Session()
        self.session.headers.update({'X-MediaBrowser-Token': emby_apikey, 'Content-Type': 'application/json'})
        return self.session

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """
        url = '{0}/emby/Notifications/Admin'.format(host or settings.EMBY_HOST)
        data = {'Name': 'SickChill', 'Description': message, 'ImageUrl': settings.LOGO_URL}

        try:
            session = self.__make_session(emby_apikey)
            response = session.post(url, data=data)
            response.raise_for_status()

            logger.debug('EMBY: HTTP response: {}'.format(response.text.replace('\n', '')))
            return True
        except requests.exceptions.HTTPError as e:
            logger.warning("EMBY: Warning: Couldn't contact Emby at {} {}".format(url, e))
            return False

##############################################################################
# Public functions
##############################################################################

    def test_notify(self, host, emby_apikey):
        return self._notify_emby('This is a test notification from SickChill', host, emby_apikey)

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        if settings.USE_EMBY:
            if not settings.EMBY_HOST:
                logger.debug('EMBY: No host specified, check your settings')
                return False

            params = {}
            if show:
                if show.indexer == 1:
                    provider = 'tvdb'
                elif show.indexer == 2:
                    logger.warning('EMBY: TVRage Provider no longer valid')
                    return False
                else:
                    logger.warning('EMBY: Provider unknown')
                    return False
                params.update({'{0}id'.format(provider): show.indexerid})

            url = '{0}/emby/Library/Series/Updated'.format(settings.EMBY_HOST)

            try:
                session = self.__make_session()
                response = session.get(url, params=params)
                response.raise_for_status()
                logger.debug('EMBY: HTTP response: {}'.format(response.text.replace('\n', '')))
                return True

            except requests.exceptions.HTTPError as error:
                logger.warning("EMBY: Warning: Couldn't contact Emby at {} {}".format(url, error))

                return False
