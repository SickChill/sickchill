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

class GenericIndexer(object):
    def __init__(self, indexer):

        INDEXER_NONE = None
        INDEXER_TVDB = 'Tvdb'
        INDEXER_TVRAGE = 'TVRage'

        INDEXER_NAME = {}
        INDEXER_NAME[INDEXER_NONE] = ''
        INDEXER_NAME[INDEXER_TVDB] = 'theTVDB'
        INDEXER_NAME[INDEXER_TVRAGE] = 'TVRage'

        INDEXER_API_KEY = {}
        INDEXER_API_KEY[INDEXER_NONE] = ''
        INDEXER_API_KEY[INDEXER_TVDB] = '9DAF49C96CBF8DAC'
        INDEXER_API_KEY[INDEXER_TVRAGE] = 'Uhewg1Rr0o62fvZvUIZt'

        INDEXER_BASEURL = {}
        INDEXER_BASEURL[INDEXER_NONE] = ''
        INDEXER_BASEURL[INDEXER_TVDB] = 'http://thetvdb.com/api/' + INDEXER_API_KEY[INDEXER_TVDB]
        INDEXER_BASEURL[INDEXER_TVRAGE] = 'http://tvrage.com/showinfo?key=' + INDEXER_API_KEY[INDEXER_TVRAGE] + 'sid='

        INDEXER_API_PARMS = {}
        INDEXER_API_PARMS[INDEXER_NONE] = ''
        INDEXER_API_PARMS[INDEXER_TVDB] = {'apikey': INDEXER_API_KEY[INDEXER_TVDB],
                                           'language': 'en',
                                           'useZip': True}

        INDEXER_API_PARMS[INDEXER_TVRAGE] = {'apikey': INDEXER_API_KEY[INDEXER_TVRAGE],
                                           'language': 'en'}

        self.config = {}
        self.config['valid_languages'] = [
            "da", "fi", "nl", "de", "it", "es", "fr","pl", "hu","el","tr",
            "ru","he","ja","pt","zh","cs","sl", "hr","ko","en","sv","no"]

        self.config['langabbv_to_id'] = {'el': 20, 'en': 7, 'zh': 27,
        'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
        'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
        'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}

        self.config['api_parms'] = INDEXER_API_PARMS[indexer]
        self.config['name'] = INDEXER_NAME[indexer]