import re
from urllib.parse import urljoin

from requests.utils import dict_from_cookiejar

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):

    def __init__(self):

        # Provider Init
        super().__init__("Speedcd")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = 0
        self.minleech = 0
        self.freeleech = False

        # URLs
        self.url = 'https://speed.cd'
        self.urls = {
            'login': urljoin(self.url, 'takeElogin.php'),
            'search': urljoin(self.url, 'browse.php'),
        }

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK']

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            'username': self.username,
            'password': self.password,
        }

        # Yay lets add another request to the process since they are unreasonable.
        response = self.get_url(self.url, returns='text')
        with BS4Parser(response, 'html5lib') as html:
            form = html.find('form', id='loginform')
            if form:
                self.urls['login'] = urljoin(self.url, form['action'])

        response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search('Incorrect username or Password. Please try again.', response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # http://speed.cd/browse.php?c49=1&c50=1&c52=1&c41=1&c55=1&c2=1&c30=1&freeleech=on&search=arrow&d=on
        # Search Params
        search_params = {
            'c30': 1,  # Anime
            'c41': 1,  # TV/Packs
            'c49': 1,  # TV/HD
            'c50': 1,  # TV/Sports
            'c52': 1,  # TV/B-Ray
            'c55': 1,  # TV/Kids
            'search': '',
        }

        # Units
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

        def process_column_header(td):
            result = ''
            img = td.find('img')
            if img:
                result = img.get('alt')
            if not result:
                result = td.get_text(strip=True)
            return result

        if self.freeleech:
            search_params['freeleech'] = 'on'

        for mode in search_strings:
            items = []
            logger.debug(_(f"Search Mode: {mode}"))

            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.debug(_(f"Search String: {search_string}"))

                search_params['search'] = re.sub(r'[^\w\s]', '', search_string)

                data = self.get_url(self.urls['search'], params=search_params, returns='text')
                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    torrent_table = html.find('div', class_='boxContent')
                    torrent_table = torrent_table.find('table') if torrent_table else []
                    # noinspection PyCallingNonCallable
                    torrent_rows = torrent_table('tr') if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    labels = [process_column_header(label) for label in torrent_rows[0]('th')]

                    # Skip column headers
                    for result in torrent_rows[1:]:
                        try:
                            cells = result('td')

                            title = cells[labels.index('Title')].find('a').get_text()
                            download_url = urljoin(self.url, cells[labels.index('Download') - 1].a['href'])
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(cells[labels.index('Seeders') - 1].get_text(strip=True))
                            leechers = try_int(cells[labels.index('Leechers') - 1].get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                                continue

                            torrent_size = cells[labels.index('Size') - 1].get_text()
                            torrent_size = torrent_size[:-2] + ' ' + torrent_size[-2:]
                            size = convert_size(torrent_size, units=units) or -1

                            item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                            if mode != 'RSS':
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results
