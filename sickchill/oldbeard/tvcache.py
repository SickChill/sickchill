import datetime
import itertools
import time
import traceback

from sickchill import logger, settings
from sickchill.helper.exceptions import AuthException
from sickchill.show.Show import Show

from . import db, show_name_helpers
from .databases import cache
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from .rssfeeds import getFeed

provider_cache_db = {}


class CacheDBConnection(db.DBConnection):
    def __init__(self):
        super().__init__("cache.db")
        db.upgrade_database(self, cache.InitialSchema)
        self.action("DELETE from results WHERE added < datetime('now','-30 days')")


class TVCache(object):
    def __init__(self, provider, **kwargs):
        self.provider = provider
        self.provider_id = self.provider.get_id()
        self.provider_db = None
        self.min_time = kwargs.pop("min_time", 10)
        self.search_params = kwargs.pop("search_params", dict(RSS=[""]))

    def _get_db(self):
        # init provider database if not done already
        if not provider_cache_db.get("instance"):
            provider_cache_db["instance"] = CacheDBConnection()

        return provider_cache_db.get("instance")

    def _clear_cache(self):
        if self.should_clear_cache():
            cache_db_con = self._get_db()
            cache_db_con.action("DELETE FROM results WHERE provider = ? AND added < datetime('now', '-30 days')", [self.provider_id])

    def _get_seeders_and_leechers(self, item):
        return self.provider._get_seeders_and_leechers(item)

    def _get_size(self, item):
        return self.provider._get_size(item)

    def _get_title_and_url(self, item):
        return self.provider._get_title_and_url(item)

    def _get_rss_data(self):
        return {"entries": self.provider.search(self.search_params)} if self.search_params else None

    def _check_auth(self, data):
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
                for item in data["entries"] or []:
                    ci = self._parse_item(item)
                    if ci:
                        cl.append(ci)

                if cl:
                    cache_db_con = self._get_db()
                    cache_db_con.mass_upsert("results", cl)

        except AuthException as e:
            logger.warning("Authentication error: " + str(e))
        except Exception as e:
            logger.debug("Error while searching " + self.provider.name + ", skipping: " + repr(e))
            logger.debug(traceback.format_exc())

    def get_rss_feed(self, url, params=None):
        if self.provider.login():
            return getFeed(url, params=params, request_hook=self.provider.get_url)
        return {"entries": []}

    @staticmethod
    def _translate_title(title):
        return "" + title.replace(" ", ".")

    @staticmethod
    def _translate_link_url(url):
        return url.replace("&amp;", "&")

    def _parse_item(self, item):
        title, url = self._get_title_and_url(item)
        size = self._get_size(item)
        seeders, leechers = self._get_seeders_and_leechers(item)

        if title and url:
            title = self._translate_title(title)
            url = self._translate_link_url(url)

            # logger.debug("Attempting to add item to cache: " + title)
            return self._add_cache_entry(title, url, size, seeders, leechers)

        else:
            logger.debug("The data returned from the " + self.provider.name + " feed is incomplete, this result is unusable")

        return False

    @property
    def last_update(self):
        cache_db_con = self._get_db()
        sql_results = cache_db_con.select("SELECT time FROM lastUpdate WHERE provider = ?", [self.provider_id])

        if sql_results:
            last_time = int(sql_results[0]["time"])
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
            last_time = int(sql_results[0]["time"])
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
        cache_db_con.upsert("lastUpdate", {"time": int(time.mktime(to_date.timetuple()))}, {"provider": self.provider_id})

    def set_last_search(self, to_date=None):
        """
        Sets the last search date for the current provider in the cache database

        :param to_date: date to set to, or None for today
        """
        if not to_date:
            to_date = datetime.datetime.today()

        cache_db_con = self._get_db()
        cache_db_con.upsert("lastSearch", {"time": int(time.mktime(to_date.timetuple()))}, {"provider": self.provider_id})

    def should_update(self):
        # if we've updated recently then skip the update
        if datetime.datetime.today() - self.last_update < datetime.timedelta(minutes=self.min_time):
            logger.debug("Last update was too soon, using old cache: " + str(self.last_update) + ". Updated less then " + str(self.min_time) + " minutes ago")
            return False

        return True

    def should_clear_cache(self):
        # if daily search hasn't used our previous results yet then don't clear the cache
        if self.last_update > self.last_search:
            return False

        return True

    def _add_cache_entry(self, name, url, size, seeders, leechers, parse_result=None, indexer_id=0):

        # check if we passed in a parsed result or should we try and create one
        if not parse_result:

            # create show_obj from indexer_id if available
            show_obj = None
            if indexer_id:
                show_obj = Show.find(settings.showList, indexer_id)

            try:
                parse_result = NameParser(showObj=show_obj).parse(name)
            except (InvalidNameException, InvalidShowException) as error:
                logger.debug("{0}".format(error))
                return None

            if not parse_result or not parse_result.series_name:
                return None

        # if we made it this far then lets add the parsed result to cache for usage later on
        season = parse_result.season_number if parse_result.season_number else 1
        episodes = parse_result.episode_numbers

        if season and episodes:
            # store episodes as a separated string
            episode_text = "|" + "|".join({str(episode) for episode in sorted(episodes) if episode}) + "|"

            # get the current timestamp
            cur_timestamp = int(time.mktime(datetime.datetime.today().timetuple()))

            # get quality of release
            quality = parse_result.quality

            # get release group
            release_group = parse_result.release_group

            # get version
            version = parse_result.version

            logger.debug(_("Added RSS item: [{}] to cache: {}").format(name, self.provider_id))
            return (
                {
                    "provider": self.provider_id,
                    "name": name,
                    "season": season,
                    "episodes": episode_text,
                    "indexerid": parse_result.show.indexerid,
                    "url": url,
                    "time": cur_timestamp,
                    "quality": quality,
                    "release_group": release_group,
                    "version": version,
                    "seeders": seeders,
                    "leechers": leechers,
                    "size": size,
                },
                {"url": url},
            )

    def search_cache(self, episode, manual_search=False, down_cur_quality=False):
        needed_eps = self.find_needed_episodes(episode, manual_search, down_cur_quality)
        return needed_eps.get(episode, [])

    def list_propers(self, date=None):
        cache_db_con = self._get_db()
        sql = "SELECT * FROM results WHERE provider = ? AND name LIKE '%.PROPER.%' OR name LIKE '%.REPACK.%'"
        # Add specific provider proper_strings also, like REAL, RERIP, etc.
        if hasattr(self.provider, "proper_strings"):
            if self.provider.proper_strings:
                for item in self.provider.proper_strings:
                    if "|" in item:
                        items = item.split("|")
                        for _item in items:
                            if _item.upper() not in sql:
                                sql += " OR name LIKE '%.{}.%'".format(_item)
                    elif item.upper() not in sql:
                        sql += " OR name LIKE '%.{}.%'".format(item)

        if date is not None:
            sql += " AND time >= " + str(int(time.mktime(date.timetuple())))

        propers_results = cache_db_con.select(sql, [self.provider_id])
        return [x for x in propers_results if x["indexerid"]]

    def find_needed_episodes(self, episode, manualSearch=False, downCurQuality=False):
        needed_eps = {}
        cl = []

        cache_db_con = self._get_db()
        if not episode:
            sql_results = cache_db_con.select("SELECT * FROM results WHERE provider = ?", [self.provider_id])
        elif not isinstance(episode, list):
            sql_results = cache_db_con.select(
                "SELECT * FROM results WHERE provider = ? AND indexerid = ? AND season = ? AND episodes LIKE ?",
                [self.provider_id, episode.show.indexerid, episode.season, "%|" + str(episode.episode) + "|%"],
            )
        else:
            for ep_obj in episode:
                cl.append(
                    [
                        "SELECT * FROM results WHERE provider = ? AND indexerid = ? AND season = ? AND episodes LIKE ? AND quality IN ("
                        + ",".join([str(x) for x in ep_obj.wantedQuality])
                        + ")",
                        [self.provider_id, ep_obj.show.indexerid, ep_obj.season, "%|" + str(ep_obj.episode) + "|%"],
                    ]
                )

            sql_results = cache_db_con.mass_action(cl, fetchall=True)
            sql_results = list(itertools.chain(*sql_results))

        # for each cache entry
        for cur_result in sql_results:
            # get the show object, or if it's not one of our shows then ignore it
            show_obj = Show.find(settings.showList, int(cur_result["indexerid"]))
            if not show_obj:
                continue

            # ignored/required words, and non-tv junk
            if not show_name_helpers.filter_bad_releases(cur_result["name"], show=show_obj):
                continue

            # skip if provider is anime only and show is not anime
            if self.provider.anime_only and not show_obj.is_anime:
                logger.debug("" + str(show_obj.name) + " is not an anime, skiping")
                continue

            # get season and ep data (ignoring multi-eps for now)
            cur_season = int(cur_result["season"])
            if cur_season == -1:
                continue

            cur_ep = cur_result["episodes"].split("|")[1]
            if not cur_ep:
                continue

            cur_ep = int(cur_ep)

            cur_quality = int(cur_result["quality"])
            cur_release_group = cur_result["release_group"]
            cur_version = cur_result["version"]

            # if the show says we want that episode then add it to the list
            if not show_obj.wantEpisode(cur_season, cur_ep, cur_quality, manualSearch, downCurQuality):
                logger.debug("Ignoring " + cur_result["name"])
                continue

            ep_obj = show_obj.getEpisode(cur_season, cur_ep)

            # build a result object
            title = cur_result["name"]
            url = cur_result["url"]

            logger.info("Found result " + title + " at " + url)

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
