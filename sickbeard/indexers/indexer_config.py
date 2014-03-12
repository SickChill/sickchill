INDEXER_TVDB = 'Tvdb'
INDEXER_TVRAGE = 'TVRage'

INDEXER_API_KEY = {}
INDEXER_API_KEY[INDEXER_TVDB] = '9DAF49C96CBF8DAC'
INDEXER_API_KEY[INDEXER_TVRAGE] = 'Uhewg1Rr0o62fvZvUIZt'

INDEXER_BASEURL = {}
INDEXER_BASEURL[INDEXER_TVDB] = 'http://thetvdb.com/api/' + INDEXER_API_KEY[INDEXER_TVDB]
INDEXER_BASEURL[INDEXER_TVRAGE] = 'http://tvrage.com/feeds/' + INDEXER_API_KEY[INDEXER_TVRAGE]

INDEXER_API_PARMS = {}
INDEXER_API_PARMS[INDEXER_TVDB] = {'apikey': INDEXER_API_KEY[INDEXER_TVDB],
                                   'language': 'en',
                                   'useZip': True}

INDEXER_API_PARMS[INDEXER_TVRAGE] = {'apikey': INDEXER_API_KEY[INDEXER_TVRAGE],
                                     'language': 'en'}


INDEXER_CONFIG = {}
INDEXER_CONFIG['valid_languages'] = [
    "da", "fi", "nl", "de", "it", "es", "fr","pl", "hu","el","tr",
    "ru","he","ja","pt","zh","cs","sl", "hr","ko","en","sv","no"]

INDEXER_CONFIG['langabbv_to_id'] = {'el': 20, 'en': 7, 'zh': 27,
'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}