from tvdb_api.tvdb_api import Tvdb
import requests

INDEXER_TVDB = 1

#Must keep
INDEXER_TVRAGE = 2

initConfig = {}
indexerConfig = {}

initConfig['valid_languages'] = [
    "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
    "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
]

initConfig['langabbv_to_id'] = {
    'el': 20, 'en': 7, 'zh': 27,
    'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
    'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
    'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30
}

indexerConfig[INDEXER_TVDB] = {
    'id': INDEXER_TVDB,
    'name': 'theTVDB',
    'module': Tvdb,
    'api_params': {'apikey': 'F9C450E78D99172E',
                   'language': 'en',
                   'useZip': True,
                  },
    'session': requests.Session()
}

# TVDB Indexer Settings
indexerConfig[INDEXER_TVDB]['trakt_id'] = 'tvdb_id'
indexerConfig[INDEXER_TVDB]['xem_origin'] = 'tvdb'
indexerConfig[INDEXER_TVDB]['icon'] = 'thetvdb16.png'
indexerConfig[INDEXER_TVDB]['scene_loc'] = 'http://sickragetv.github.io/sb_tvdb_scene_exceptions/exceptions.txt'
indexerConfig[INDEXER_TVDB]['show_url'] = 'http://thetvdb.com/?tab=series&id='
indexerConfig[INDEXER_TVDB]['base_url'] = 'http://thetvdb.com/api/%(apikey)s/series/' % indexerConfig[INDEXER_TVDB]['api_params']
