from datetime import date, timedelta
from operator import itemgetter

from sickchill import settings
from sickchill.helper.common import dateFormat, timeFormat
from sickchill.helper.quality import get_quality_string
from sickchill.oldbeard.common import Quality, UNAIRED, WANTED
from sickchill.oldbeard.db import DBConnection
from sickchill.oldbeard.network_timezones import parse_date_time
from sickchill.oldbeard.sbdatetime import sbdatetime

SNATCHED = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST  # type = list


class ComingEpisodes(object):
    """
    Snatched: snatched but not yet processed (no re-downloads)
    Missed:   yesterday...(less than settings.COMING_EPS_MISSED_RANGE)
    Today:    today
    Soon:     tomorrow till next week
    Later:    later than next week
    """

    categories = ["snatched", "missed", "today", "soon", "later"]
    sorts = {
        "date": itemgetter("snatchedsort", "localtime", "episode"),
        "network": itemgetter("network", "localtime", "episode"),
        "show": itemgetter("show_name", "localtime", "episode"),
    }

    def __init__(self):
        pass

    @staticmethod
    def get_coming_episodes(categories, sort, group, paused=settings.COMING_EPS_DISPLAY_PAUSED):
        """
        :param categories: The categories of coming episodes. See ``ComingEpisodes.categories``
        :param sort: The sort to apply to the coming episodes. See ``ComingEpisodes.sorts``
        :param group: ``True`` to group the coming episodes by category, ``False`` otherwise
        :param paused: ``True`` to include paused shows, ``False`` otherwise
        :return: The list of coming episodes
        """

        categories = ComingEpisodes._get_categories(categories)
        sort = ComingEpisodes._get_sort(sort)

        today = date.today().toordinal()
        recently = (date.today() - timedelta(days=settings.COMING_EPS_MISSED_RANGE)).toordinal()
        next_week = (date.today() + timedelta(days=7)).toordinal()

        db = DBConnection(row_type="dict")
        fields_to_select = ", ".join(
            [
                "airdate",
                "airs",
                "e.description as description",
                "episode",
                "imdb_id",
                "e.indexer",
                "indexer_id",
                "e.location",
                "name",
                "network",
                "paused",
                "quality",
                "runtime",
                "season",
                "show_name",
                "showid",
                "e.status as epstatus",
                "s.status",
            ]
        )

        status_list = [WANTED, UNAIRED] + SNATCHED

        sql_l = []
        for show_obj in settings.showList:
            next_air_date = show_obj.nextEpisode()
            sql_l.append(
                [
                    "SELECT DISTINCT {0} ".format(fields_to_select) + "FROM tv_episodes e, tv_shows s "
                    "WHERE showid = ? "
                    "AND airdate <= ? "
                    "AND airdate >= ? "
                    "AND s.indexer_id = e.showid "
                    "AND e.status IN (" + ",".join(["?"] * len(status_list)) + ")",
                    [show_obj.indexerid, next_air_date or today, recently] + status_list,
                ]
            )

        results = []
        for sql_i in sql_l:
            if results:
                results += db.select(*sql_i)
            else:
                results = db.select(*sql_i)

        for index, item in enumerate(results):
            results[index]["localtime"] = sbdatetime.convert_to_setting(parse_date_time(item["airdate"], item["airs"], item["network"]))
            results[index]["snatchedsort"] = int(not results[index]["epstatus"] in SNATCHED)

        results.sort(key=ComingEpisodes.sorts[sort])

        if not group:
            return results

        grouped_results = ComingEpisodes._get_categories_map(categories)

        for result in results:
            if result["paused"] and not paused:
                continue

            result["airs"] = str(result["airs"]).replace("am", " AM").replace("pm", " PM").replace("  ", " ")
            result["airdate"] = result["localtime"].toordinal()

            if result["epstatus"] in SNATCHED:
                if result["location"]:
                    continue
                else:
                    category = "snatched"
            elif result["airdate"] < today:
                category = "missed"
            elif result["airdate"] >= next_week:
                category = "later"
            elif result["airdate"] == today:
                category = "today"
            else:
                category = "soon"

            if categories and category not in categories:
                continue

            if not result["network"]:
                result["network"] = ""

            result["quality"] = get_quality_string(result["quality"])
            result["airs"] = sbdatetime.sbftime(result["localtime"], t_preset=timeFormat).lstrip("0").replace(" 0", " ")
            result["weekday"] = 1 + result["localtime"].weekday()
            result["tvdbid"] = result["indexer_id"]
            result["airdate"] = sbdatetime.sbfdate(result["localtime"], d_preset=dateFormat)
            result["localtime"] = result["localtime"].toordinal()

            grouped_results[category].append(result)

        return grouped_results

    @staticmethod
    def _get_categories(categories):
        if not categories:
            return []

        if not isinstance(categories, list):
            return categories.split("|")

        return categories

    @staticmethod
    def _get_categories_map(categories):
        if not categories:
            return {}

        return {category: [] for category in categories}

    @staticmethod
    def _get_sort(sort):
        sort = sort.lower() if sort else ""

        if sort not in list(ComingEpisodes.sorts):
            return "date"

        return sort
