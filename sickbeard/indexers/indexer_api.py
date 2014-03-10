# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from lib.tvdb_api.tvdb_api import Tvdb
from lib.tvrage_api.tvrage_api import TVRage

class indexerApi:
    def __new__(self, indexer):
        cls = type(eval(indexer))
        new_type = type(cls.__name__ + '_wrapped', (indexerApi, cls), {})
        return object.__new__(new_type)

    def __init__(self, indexer=None, language=None, *args, **kwargs):
        if indexer is not None:
            self.name = indexer
            self._wrapped = eval(indexer)(*args, **kwargs)
        else:
            self.name = "Indexer"

        self.config = {}

        self.config['valid_languages'] = [
            "da", "fi", "nl", "de", "it", "es", "fr","pl", "hu","el","tr",
            "ru","he","ja","pt","zh","cs","sl", "hr","ko","en","sv","no"
        ]

        self.config['langabbv_to_id'] = {'el': 20, 'en': 7, 'zh': 27,
        'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
        'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
        'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}

        if language is None:
            self.config['language'] = 'en'
        else:
            if language not in self.config['valid_languages']:
                raise ValueError("Invalid language %s, options are: %s" % (
                    language, self.config['valid_languages']
                ))
            else:
                self.config['language'] = language

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)

    def __getitem__(self, attr):
        return self._wrapped.__getitem__(attr)