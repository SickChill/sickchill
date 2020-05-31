# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
from functools import wraps

# Third Party Imports
from requests.exceptions import HTTPError as RHTTPError, RequestException, RequestsWarning
from urllib3.exceptions import HTTPError, HTTPWarning

# First Party Imports
from sickbeard import logger
from sickchill.helper.exceptions import ex


class ExceptionDecorator(object):

    def __init__(self, default_return=list(), catch=(HTTPError, HTTPWarning, RequestException, RequestsWarning), image_api=False):
        self.default_return = default_return
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
                        logger.log("Could not find the image on the indexer, re-trying to find it in english", logger.DEBUG)
                        kwargs['lang'] = 'en'
                        return wrapper(*args, **kwargs)

                logger.log("Could not find item on the indexer: (Indexer probably doesn't have this item) [{error}]".format(error=ex(e)), logger.DEBUG)
                result = self.default_return
            except RHTTPError as e:
                logger.log("Could not find item on the indexer: (Indexer probably doesn't have this item) [{error}]".format(error=ex(e)), logger.DEBUG)
                result = self.default_return

            return result

        wrapper.__doc__ = target.__doc__
        return wrapper
