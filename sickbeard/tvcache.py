# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import datetime
import itertools
import time

import sickbeard
from sickbeard import db, logger, show_name_helpers
from sickbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickbeard.rssfeeds import getFeed
from sickrage.helper.exceptions import AuthException, ex
from sickrage.show.Show import Show


import six


class CacheDBConnection(db.DBConnection):
    def __init__(self, provider_name):
        super(CacheDBConnection, self).__init__('cache.db')

        # Create the table if it's not already there
        try:
            if not self.hasTable(provider_name):
                self.action(
                    "CREATE TABLE [" + provider_name + "] (name TEXT, season NUMERIC, episodes TEXT, indexerid NUMERIC, url TEXT, time NUMERIC, quality TEXT, release_group TEXT)")
            else:
                sql_results = self.select("SELECT url, COUNT(url) AS count FROM [" + provider_name + "] GROUP BY url HAVING count > 1")

                for cur_dupe in sql_results:
                    self.action("DELETE FROM [" + provider_name + "] WHERE url = ?", [cur_dupe[b"url"]])

            # add unique index to prevent further dupes from happening if one does not exist
            self.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_url ON [" + provider_name + "] (url)")

            # add release_group column to table if missing
            if not self.hasColumn(provider_name, 'release_group'):
                self.addColumn(provider_name, 'release_group', "TEXT", "")

            # add version column to table if missing
            if not self.hasColumn(provider_name, 'version'):
                self.addColumn(provider_name, 'version', "NUMERIC", "-1")

        except Exception as e:
            if str(e) != "table [" + provider_name + "] already exists":
                raise

        # Create the table if it's not already there
        try:
            if not self.hasTable('lastUpdate'):
                self.action("CREATE TABLE lastUpdate (provider TEXT, time NUMERIC)")
        except Exception as e:
            if str(e) != "table lastUpdate already exists":
                raise


class TVCache(object):
    def __init__(self, provider, **kwargs):
        self.provider = provider
        self.provider_id = self.provider.get_id()
        self.provider_db = None
        self.min_time = kwargs.pop('min_time', 10)
        self.search_params = kwargs.pop('search_params', dict(RSS=['']))

    def _get_db(self):
        # init provider database if not done already
        if not self.provider_db:
            self.provider_db = CacheDBConnection(self.provider_id)

        return self.provider_db

    def _clear_cache(self):
        if self.should_clear_cache():
            cache_db_con = self._get_db()
            cache_db_con.action("DELETE FROM [" + self.provider_id + "] WHERE 1")

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)  # pylint:disable=protected-access

    def _get_rss_data(self):
        return {'entries': self.provider.search(self.search_params)} if self.search_params else None

    def _check_auth(self, data):  # pylint:disable=unused-argument, no-self-use
        return True

    def _check_item_auth(self, title, url):  # pylint:disable=unused-argument, no-self-use
        return True

    def update_cache(self):
        # check if we should update
        if not self.should_update():
            return

        try:
            data = self._get_rss_data()
            if self._check_auth(data):
                # clear cache
                self._clear_cache()

                # set updated
                self.set_last_update()

                cl = []
                for item in data['entries'] or []:
                    ci = self._parse_item(item)
                    if ci is not None:
                        cl.append(ci)

                if cl:
                    cache_db_con = self._get_db()
                    cache_db_con.mass_action(cl)

        except AuthException as e:
            logger.log("Authentication error: " + ex(e), logger.WARNING)
        except Exception as e:
            logger.log("Error while searching " + self.provider.name + ", skipping: " + repr(e), logger.DEBUG)

    def get_rss_feed(self, url, params=None):
        if self.provider.login():
            return getFeed(url, params=params, request_hook=self.provider.get_url)
        return {'entries': []}

    @staticmethod
    def _translate_title(title):
        return '' + title.replace(' ', '.')

    @staticmethod
    def _translate_link_url(url):
        return url.replace('&amp;', '&')

    def _parse_item(self, item):
        title, url = self._get_title_and_url(item)

        self._check_item_auth(title, url)

        if title and url:
            title = self._translate_title(title)
            url = self._translate_link_url(url)

            # logger.log(u"Attempting to add item to cache: " + title, logger.DEBUG)
            return self._add_cache_entry(title, url)

        else:
            logger.log(
                "The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable",
                logger.DEBUG)

        return False

    @property
    def last_update(self):
        cache_db_con = self._get_db()
        sql_results = cache_db_con.select("SELECT time FROM lastUpdate WHERE provider = ?", [self.provider_id])

        if sql_results:
            last_time = int(sql_results[0][b"time"])
            if last_time > int(time.mktime(datetime.datetime.today().timetuple())):
                last_time = 0
        else:
            last_time = 0

        return datetime.datetime.fromtimestamp(last_time)

    @property
    def last_search(self):
        cache_db_con = self._get_db()
        sql_results = cache_db_con.select("SELECT time FROM lastSearch WHERE provider = ?", [self.provider_id])

        if sql_results:
            last_time = int(sql_results[0][b"time"])
            if last_time > int(time.mktime(datetime.datetime.today().timetuple())):
                last_time = 0
        else:
            last_time = 0

        return datetime.datetime.fromtimestamp(last_time)

    def set_last_update(self, to_date=None):
        """
        Sets the last update date for the current provider in the cache database
        
        :param to_date: date to set to, or None for today
        """
        if not to_date:
            to_date = datetime.datetime.today()

        cache_db_con = self._get_db()
        cache_db_con.upsert(
            "lastUpdate",
            {'time': int(time.mktime(to_date.timetuple()))},
            {'provider': self.provider_id}
        )

    def set_last_search(self, to_date=None):
        """
        Sets the last search date for the current provider in the cache database

        :param to_date: date to set to, or None for today
        """
        if not to_date:
            to_date = datetime.datetime.today()

        cache_db_con = self._get_db()
        cache_db_con.upsert(
            "lastSearch",
            {'time': int(time.mktime(to_date.timetuple()))},
            {'provider': self.provider_id}
        )

    def should_update(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.last_update < datetime.timedelta(minutes=self.min_time):
            logger.log("Last update was too soon, using old cache: " + str(self.last_update) + ". Updated less then " + str(self.min_time) + " minutes ago", logger.DEBUG)
            return False

        return True

    def should_clear_cache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.last_update > self.last_search:
            return False

        return True

    def _add_cache_entry(self, name, url, parse_result=None, indexer_id=0):

        # check if we passed in a parsed result or should we try and create one
        if not parse_result:

            # create show_obj from indexer_id if available
            show_obj = None
            if indexer_id:
                show_obj = Show.find(sickbeard.showList, indexer_id)

            try:
                parse_result = NameParser(showObj=show_obj).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.log("{0}".format(error), logger.DEBUG)
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usager later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a seperated string
            episode_text = "|" + "|".join({str(episode) for episode in episodes if episode}) + "|"

            # get the current timestamp
            cur_timestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            assert isinstance(name, six.text_type)

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logger.log("Added RSS item: [" + name + "] to cache: [" + self.provider_id + "]", logger.DEBUG)

            return [
                "INSERT OR IGNORE INTO [" + self.provider_id + "] (name, season, episodes, indexerid, url, time, quality, release_group, version) VALUES (?,?,?,?,?,?,?,?,?)",
                [name, season, episode_text, parse_result.show.indexerid, url, cur_timestamp, quality, release_group, version]]

    def search_cache(self, episode, manual_search=False, down_cur_quality=False):
        needed_eps = self.find_needed_episodes(episode, manual_search, down_cur_quality)
        return needed_eps.get(episode, [])

    def list_propers(self, date=None):
        cache_db_con = self._get_db()
        sql = "SELECT * FROM [" + self.provider_id + "] WHERE name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"

        if date is not None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        propers_results = cache_db_con.select(sql)
        return [x for x in propers_results if x[b'indexerid']]

    def find_needed_episodes(self, episode, manualSearch=False, downCurQuality=False):  # pylint:disable=too-many-locals, too-many-branches
        needed_eps = {}
        cl = []

        cache_db_con = self._get_db()
        if not episode:
            sql_results = cache_db_con.select("SELECT * FROM [" + self.provider_id + "]")
        elif not isinstance(episode, list):
            sql_results = cache_db_con.select(
                "SELECT * FROM [" + self.provider_id + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ?",
                [episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"])
        else:
            for ep_obj in episode:
                cl.append([
                    "SELECT * FROM [" + self.provider_id + "] WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN (" + ",".join(
                        [str(x) for x in ep_obj.wantedQuality]) + ")",
                    [ep_obj.show.indexerid, ep_obj.season, "%|" + str(ep_obj.episode) + "|%"]])

            sql_results = cache_db_con.mass_action(cl, fetchall=True)
            sql_results = list(itertools.chain(*sql_results))

        # for each cache entry
        for cur_result in sql_results:
            # get the show object, or if it's not one of our shows then ignore it
            show_obj = Show.find(sickbeard.showList, int(cur_result[b"indexerid"]))
            if not show_obj:
                continue

            # ignored/required words, and non-tv junk
            if not show_name_helpers.filter_bad_releases(cur_result[b"name"], show=show_obj):
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not show_obj.is_anime:
                logger.log("" + str(show_obj.name) + " is not an anime, skiping", logger.DEBUG)
                continue

            # get season and ep data (ignoring multi-eps for now)
            cur_season = int(cur_result[b"season"])
            if cur_season == -1:
                continue

            cur_ep = cur_result[b"episodes"].split("|")[1]
            if not cur_ep:
                continue

            cur_ep = int(cur_ep)

            cur_quality = int(cur_result[b"quality"])
            cur_release_group = cur_result[b"release_group"]
            cur_version = cur_result[b"version"]

            # if the show says we want that episode then add it to the list
            if not show_obj.wantEpisode(cur_season, cur_ep, cur_quality, manualSearch, downCurQuality):
                logger.log("Ignoring " + cur_result[b"name"], logger.DEBUG)
                continue

            ep_obj = show_obj.getEpisode(cur_season, cur_ep)

            # build a result object
            title = cur_result[b"name"]
            url = cur_result[b"url"]

            logger.log("Found result " + title + " at " + url)

            result = self.provider.get_result([ep_obj])
            result.show = show_obj
            result.url = url
            result.name = title
            result.quality = cur_quality
            result.release_group = cur_release_group
            result.version = cur_version
            result.content = None

            # add it to the list
            if ep_obj not in needed_eps:
                needed_eps[ep_obj] = [result]
            else:
                needed_eps[ep_obj].append(result)

        # datetime stamp this search so cache gets cleared
        self.set_last_search()

        return needed_eps
