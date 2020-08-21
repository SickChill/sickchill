from functools import wraps

from requests.exceptions import HTTPError as RHTTPError, RequestException, RequestsWarning
from urllib3.exceptions import HTTPError, HTTPWarning

from sickchill import logger


class ExceptionDecorator(object):

    def __init__(self, default_return=None, catch=(HTTPError, HTTPWarning, RequestException, RequestsWarning, TypeError), image_api=False):
        self.default_return = default_return or []
        self.catch = catch
        self.image_api = image_api

    def __call__(self, target, *args, **kwargs):
        @wraps(target)
        def wrapper(*args, **kwargs):
            try:
                result = target(*args, **kwargs)
            except self.catch as e:
                if self.image_api and not kwargs.get('lang'):
                    if args[1].lang != 'en':
                        logger.debug("Could not find the image on the indexer, re-trying to find it in english")
                        kwargs['lang'] = 'en'
                        return wrapper(*args, **kwargs)

                logger.debug("Could not find item on the indexer: (Indexer probably doesn't have this item) [{error}]".format(error=str(e)))
                result = self.default_return
            except RHTTPError as e:
                logger.debug("Could not find item on the indexer: (Indexer probably doesn't have this item) [{error}]".format(error=str(e)))
                result = self.default_return

            return result

        wrapper.__doc__ = target.__doc__
        return wrapper
