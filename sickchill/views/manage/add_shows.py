import datetime
import json
import os
import re
import traceback
from urllib.parse import quote_plus

import dateutil.parser
from tornado.web import HTTPError

import sickchill
from sickchill import logger, settings
from sickchill.helper import sanitize_filename, try_int
from sickchill.helper.list_status import build_list_status
from sickchill.oldbeard import config, db, helpers, tmdbLists, tvmazePremieres, ui
from sickchill.oldbeard.blackandwhitelist import short_group_names
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.trakt_api import TraktAPI
from sickchill.show.recommendations.imdb import imdb_popular
from sickchill.show.Show import Show
from sickchill.tv import TVShow
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home
from sickchill.views.routes import Route

# Discovery list keys (TMDB + TVMaze). Old traktList= query values are aliased below.
_DISCOVERY_LIST_KEYS = ("trending", "popular", "top_rated", "on_the_air", "premieres")

_DISCOVERY_LIST_ALIASES = {
    "anticipated": "trending",
    "newshow": "premieres",
    "newseason": "premieres",
    "collected": "popular",
    "watched": "popular",
    "played": "popular",
    "recommended": "top_rated",
    "tvmaze": "premieres",
    "upcoming": "premieres",
}


def _discovery_list_options():
    return {
        "trending": _("Trending (TMDB)"),
        "popular": _("Popular (TMDB)"),
        "top_rated": _("Top Rated (TMDB)"),
        "on_the_air": _("On The Air (TMDB)"),
        "premieres": _("Upcoming Premieres (TVMaze)"),
    }


@Route("/addShows(/?.*)", name="addShows")
class AddShows(Home):
    def index(self):
        t = PageTemplate(rh=self, filename="addShows.mako")
        return t.render(
            title=_("Add Shows"),
            header=_("Add Shows"),
            topmenu="home",
            controller="addShows",
            action="index",
        )

    def sanitizeFileName(self):
        return sanitize_filename(self.get_body_argument("name"))

    def searchIndexersForShowName(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")
        search_term = self.get_body_argument("search_term")
        search_terms = [search_term]  # get_arguments to make this a list of terms, we can probably add advanced searching here.
        lang = self.get_body_argument("lang", default=settings.INDEXER_DEFAULT_LANGUAGE)
        indexer = int(self.get_body_argument("indexer", default=settings.INDEXER_DEFAULT))
        exact = config.checkbox_to_value(self.get_body_argument("exact"))

        # If search term ends with what looks like a year, enclose it in ()
        matches = re.match(r"^(.+ |)([12][0-9]{3})$", search_term)
        if matches:
            search_terms.append("{0}({1})".format(matches.group(1), matches.group(2)))

        search_list = search_terms  # for safety of terms list.
        for term in search_list:
            # If search term begins with an article, let's also search for it without
            matches = re.match(r"^(?:a|an|the) (.+)$", term, re.IGNORECASE)
            if matches:
                search_terms.append(matches.group(1))

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for index, indexer_object in sickchill.indexer:
            if indexer and indexer != index:
                continue

            logger.debug(
                _("Searching for Show with search term(s): {search_terms} on Indexer: {indexer_name} (exact: {exact})").format(
                    search_terms=search_terms, indexer_name=indexer_object.name, exact=exact
                )
            )
            for term in search_terms:
                # noinspection PyBroadException
                try:
                    indexer_results = indexer_object.search(term, language=lang, exact=exact)
                except Exception:
                    logger.debug(traceback.format_exc())
                    continue

                # add search results
                results.setdefault(index, []).extend(indexer_results)

        for index, shows in results.items():
            for show in shows:
                show_id = show["id"]
                series_name = show.get("seriesName") or ""
                first_aired = show.get("firstAired") or ""
                in_list = sickchill.tv.Show.find(settings.show_list, show_id) is not None
                # Legacy pipe fields for whichSeries form value (indexes 0–6)
                which_series = "|".join(
                    [
                        str(sickchill.indexer[index].name),
                        str(index),
                        str(sickchill.indexer[index].show_url),
                        str(show_id),
                        str(series_name).replace("|", " "),
                        str(first_aired).replace("|", " "),
                        "1" if in_list else "0",
                    ]
                )
                try:
                    # Already 0–100 from TVDB mapping; keep integer for UI
                    score = round(float(show.get("score") or 0))
                except (TypeError, ValueError):
                    score = 0
                final_results.append(
                    {
                        "whichSeries": which_series,
                        "indexer": sickchill.indexer[index].name,
                        "indexer_id": index,
                        "show_url": sickchill.indexer[index].show_url,
                        "id": show_id,
                        "seriesName": series_name,
                        "firstAired": first_aired,
                        "inShowList": in_list,
                        "score": score,
                        "image_url": show.get("image_url") or "",
                        "network": show.get("network") or "",
                        "overview": show.get("overview") or "",
                        "status": show.get("status") or "",
                        "year": show.get("year") or "",
                        "source": show.get("source") or "tvdb",
                    }
                )

        # Dedupe by indexer id (multi-term searches can repeat hits)
        deduped = {}
        for item in final_results:
            key = (item["indexer_id"], item["id"])
            prev = deduped.get(key)
            if prev is None or float(item.get("score") or 0) > float(prev.get("score") or 0):
                deduped[key] = item
        final_results = list(deduped.values())

        if exact in [True, "1"]:
            logger.debug(_("Filtering results because exact match was checked"))
            term_l = (search_term or "").strip().lower()
            final_results = [item for item in final_results if (item.get("seriesName") or "").strip().lower() == term_l]

        # Always sort by score (highest first); exact checkbox is filter-only
        final_results.sort(key=lambda x: int(x.get("score") or 0), reverse=True)

        lang_id = sickchill.indexer[indexer or sickchill.indexer.TVDB].lang_dict[lang]
        return json.dumps({"results": final_results, "langid": lang_id, "success": len(final_results) > 0})

    def massAddTable(self):
        t = PageTemplate(rh=self, filename="home_massAddTable.mako")
        root_dirs = self.get_arguments("rootDir")
        if not root_dirs:
            return _("No folders selected.")

        dir_list = []

        main_db_con = db.DBConnection()
        for root_dir in root_dirs:
            # noinspection PyBroadException
            try:
                file_list = os.listdir(root_dir)
            except Exception:  # noqa: S112
                continue

            for cur_file in file_list:
                # noinspection PyBroadException
                try:
                    cur_path = os.path.normpath(os.path.join(root_dir, cur_file))
                    if not os.path.isdir(cur_path):
                        continue
                    # ignore Synology folders
                    # noinspection SpellCheckingInspection
                    if cur_file.lower() in ["#recycle", "@eadir"]:
                        continue
                except Exception:  # noqa: S112
                    continue

                cur_dir = {
                    "dir": cur_path,
                    "existing_info": (None, None, None),
                    "display_dir": "<b>" + os.path.dirname(cur_path) + os.sep + "</b>" + os.path.basename(cur_path),
                }

                dir_results = main_db_con.select("SELECT indexer_id FROM tv_shows WHERE location = ? LIMIT 1", [cur_path])

                cur_dir["added_already"] = bool(dir_results)

                dir_list.append(cur_dir)

                indexer_id = show_name = indexer = None
                for cur_provider in settings.metadata_provider_dict.values():
                    if not (indexer_id and show_name):
                        (indexer_id, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)
                        if all((indexer_id, show_name, indexer)):
                            break

                if all((indexer_id, show_name, indexer)):
                    cur_dir["existing_info"] = (indexer_id, show_name, indexer)

                if indexer_id and Show.find(settings.show_list, indexer_id):
                    cur_dir["added_already"] = True
        return t.render(dirList=dir_list)

    def newShow(self, show_to_add=None, other_shows=None, search_string=None, exact=None, indexer_id=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow

        Query kwargs ``exact`` and ``indexer_id`` must be in the signature: the web router
        passes them as kwargs, and unexpected names caused TypeError → empty ``newShow()``.
        """
        # Prefer router/query kwargs; fall back to explicit get_* for POST body / in-process calls
        if show_to_add is None:
            show_to_add = self.get_body_argument("show_to_add", default=None)
        if other_shows is None:
            other_shows = self.get_body_arguments("other_shows") or None
        if search_string is None:
            search_string = self.get_query_argument("search_string", default="") or self.get_body_argument("search_string", default="")
        if exact is None:
            exact = self.get_query_argument("exact", default="") or self.get_body_argument("exact", default="")
        exact_match = str(exact or "").strip().lower() in ("1", "true", "yes", "on")

        # Discovery Add may pass a verified TVDB id while search_string holds the display title
        discovery_indexer_id = try_int(indexer_id, 0) if indexer_id not in (None, "") else 0
        if not discovery_indexer_id:
            discovery_indexer_id = try_int(self.get_query_argument("indexer_id", default="0"), 0)

        t = PageTemplate(rh=self, filename="addShows_newShow.mako")

        indexer, show_dir, pipe_indexer_id, show_name = self.split_extra_show(show_to_add)

        if pipe_indexer_id and indexer and show_name:
            use_provided_info = True
        else:
            use_provided_info = False

        if show_name:
            default_show_name = show_name
        elif show_dir:
            default_show_name = re.sub(r" \(\d{4}\)", "", os.path.basename(os.path.normpath(show_dir)).replace(".", " "))
        elif search_string:
            default_show_name = search_string
        else:
            default_show_name = ""

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        provided_indexer_id = int(pipe_indexer_id or 0)
        provided_indexer_name = show_name

        provided_indexer = int(indexer or settings.INDEXER_DEFAULT)

        return t.render(
            enable_anime_options=True,
            use_provided_info=use_provided_info,
            default_show_name=default_show_name,
            exact_match=exact_match,
            discovery_indexer_id=discovery_indexer_id or "",
            other_shows=other_shows,
            provided_show_dir=show_dir,
            provided_indexer_id=provided_indexer_id,
            provided_indexer_name=provided_indexer_name,
            provided_indexer=provided_indexer,
            whitelist=settings.WHITELIST_DEFAULT,
            blacklist=settings.BLACKLIST_DEFAULT,
            groups=[],
            title=_("New Show"),
            header=_("New Show"),
            topmenu="home",
            controller="addShows",
            action="newShow",
        )

    @staticmethod
    def _resolve_discovery_list_key(raw: str) -> str:
        key = (raw or "trending").strip().lower()
        key = _DISCOVERY_LIST_ALIASES.get(key, key)
        if key not in _DISCOVERY_LIST_KEYS:
            return "trending"
        return key

    @staticmethod
    def _mark_already_added(cards: list) -> None:
        """Soft-mark cards already in the library (tvdb id or title+year)."""
        by_tvdb = {int(show.indexerid): show for show in settings.show_list if getattr(show, "indexerid", None)}
        by_title_year = {}
        for show in settings.show_list:
            name = (getattr(show, "name", None) or getattr(show, "show_name", None) or "").strip().lower()
            year = None
            try:
                year = int(str(getattr(show, "startyear", "") or "")[:4])
            except (TypeError, ValueError):
                year = None
            if name:
                by_title_year[(name, year)] = show

        for card in cards:
            tvdb_id = card.get("tvdb_id")
            if tvdb_id and int(tvdb_id) in by_tvdb:
                card["already_added"] = True
                continue
            title = (card.get("title") or "").strip().lower()
            year = card.get("year")
            card["already_added"] = bool(title and (title, year) in by_title_year)

    def trendingShows(self):
        """Shell page for TMDB / TVMaze discovery lists (AJAX loads getTrendingShows)."""
        raw = self.get_query_argument("tmdbList", default="") or self.get_query_argument("traktList", default="trending")
        list_key = self._resolve_discovery_list_key(raw)
        list_options = _discovery_list_options()

        t = PageTemplate(rh=self, filename="addShows_trendingShows.mako")
        return t.render(
            title=_("The Lists"),
            header=_("The Lists"),
            list_key=list_key,
            list_options=list_options,
            # Compat for older JS reading #traktList
            traktList=list_key,
            trakt_options=list_options,
            controller="addShows",
            action="trendingShows",
        )

    def getTrendingShows(self):
        """AJAX fragment: TMDB or TVMaze discovery cards."""
        t = PageTemplate(rh=self, filename="trendingShows.mako")

        raw = self.get_query_argument("tmdbList", default="") or self.get_query_argument("traktList", default="")
        list_key = self._resolve_discovery_list_key(raw)

        trending_shows = []
        status_code = None
        settings_url = f"{settings.WEB_ROOT}/config/general/"

        try:
            if list_key == "premieres":
                trending_shows = tvmazePremieres.fetch_premieres()
            else:
                trending_shows = tmdbLists.fetch_list(list_key)
            if not trending_shows:
                status_code = "empty"
            else:
                self._mark_already_added(trending_shows)
        except tmdbLists.TMDBMissingKeyError as error:
            status_code = "missing_key"
            logger.warning(f"TMDB discovery list unavailable: {error}")
        except (tmdbLists.TMDBListsError, tvmazePremieres.TVMazePremieresError) as error:
            status_code = "fetch_failed"
            logger.warning(f"Could not get discovery shows ({list_key}): {error}")
        except Exception as error:
            status_code = "fetch_failed"
            logger.warning(f"Could not get discovery shows ({list_key}): {error}")

        list_status = build_list_status(status_code, settings_url=settings_url)
        return t.render(
            black_list=False,
            trending_shows=trending_shows,
            list_status=list_status,
            list_key=list_key,
        )

    def getTrendingShowImage(self):
        """Legacy Trakt poster cache endpoint — unused for TMDB/TVMaze CDN posters."""
        return ""

    def addShowFromTMDB(self):
        """Lazy-resolve TMDB → TVDB id, then addShowByID or name search."""
        tmdb_id = try_int(self.get_query_argument("tmdb_id", default="0"), 0)
        show_name = self.get_query_argument("show_name", default="") or ""
        # year reserved for future soft-match; accepted for API compatibility
        _year = self.get_query_argument("year", default="")

        if tmdb_id <= 0:
            ui.notifications.error(_("Unable to add show"), _("Missing TMDB id"))
            return self.redirect("/addShows/")

        try:
            tvdb_id = tmdbLists.resolve_tvdb_id(tmdb_id)
        except tmdbLists.TMDBMissingKeyError:
            ui.notifications.error(_("Unable to add show"), _("TMDB API key is not configured"))
            return self.redirect("/addShows/trendingShows/")
        except Exception as error:
            logger.warning(f"TMDB external_ids failed for {tmdb_id}: {error}")
            tvdb_id = None

        if tvdb_id:
            return self.redirect(f"/addShows/addShowByID?indexer_id={tvdb_id}&show_name={quote_plus(show_name)}")

        # No TVDB mapping — name search with exact-match (do not guess TVDB from title)
        search = show_name.strip() or str(tmdb_id)
        return self.redirect(f"/addShows/newShow/?search_string={quote_plus(search)}&exact=1")

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        t = PageTemplate(rh=self, filename="addShows_popularShows.mako")
        try:
            popular = imdb_popular.fetch_popular_shows()
            popular_shows = []

            for idx, show in enumerate(popular[:100], 1):
                try:
                    imdb_id = show.get("id") or show.get("tconst")
                    if not imdb_id:
                        continue

                    # Clean ID if needed
                    if isinstance(imdb_id, str) and imdb_id.startswith("/title/"):
                        imdb_id = imdb_id.split("/")[2]

                    title = show.get("title") or show.get("l", "Unknown")
                    year = show.get("year")

                    # Image
                    image_data = show.get("image")
                    image_url = image_data.get("url") if isinstance(image_data, dict) else None

                    popular_shows.append(
                        {
                            "id": imdb_id,
                            "imdb_id": imdb_id,
                            "name": title,
                            "year": year,
                            "image": image_url,
                            "currentRank": show.get("currentRank") or idx,
                            "current_imdb_id": None,
                        }
                    )
                except Exception as error:
                    logger.debug(f"Skipping malformed IMDb popular show item: {error}")
                    continue

            # Mark existing shows in a single query
            imdb_ids = [show["imdb_id"] for show in popular_shows]
            existing_map = {}
            if imdb_ids:
                main_db_con = db.DBConnection()
                placeholders = ",".join("?" * len(imdb_ids))
                for row in main_db_con.select(f"SELECT show_id, imdb_id FROM tv_shows WHERE imdb_id IN ({placeholders})", imdb_ids):
                    existing_map[row["imdb_id"]] = row["show_id"]
            for show in popular_shows:
                show["current_imdb_id"] = existing_map.get(show["imdb_id"])

            return t.render(
                title=_("Popular Shows"),
                header=_("Popular Shows"),
                popular_shows=popular_shows,
                imdb_exception=None,
                imdb_url=imdb_popular.imdb_url,
                topmenu="home",
                controller="addShows",
                action="popularShows",
            )

        except Exception as e:
            logger.exception(f"Failed to load popular IMDb shows: {e}")
            return t.render(
                popular_shows=[],
                title="Popular Shows",
                header="Popular Shows",
                imdb_exception=None,
                imdb_url=lambda x: "#",
                topmenu="home",
                controller="addShows",
                action="popularShows",
            )

    def addShowToBlacklist(self):
        # URL parameters

        indexer_id = self.get_query_argument("indexer_id")
        if not indexer_id:
            raise HTTPError(404)

        data = {"shows": [{"ids": {"tvdb": indexer_id}}]}

        trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)

        trakt_api.traktRequest("users/" + settings.TRAKT_USERNAME + "/lists/" + settings.TRAKT_BLACKLIST_NAME + "/items", data, method="POST")

        return self.redirect("/addShows/trendingShows/")

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        t = PageTemplate(rh=self, filename="addShows_addExistingShow.mako")
        return t.render(
            enable_anime_options=False, title=_("Existing Show"), header=_("Existing Show"), topmenu="home", controller="addShows", action="addExistingShow"
        )

    def addShowByID(self):
        indexer_id = self.get_query_argument("indexer_id")
        show_name = self.get_query_argument("show_name")
        indexer = self.get_query_argument("indexer", default="TVDB")

        def add_error(in_list: TVShow = None) -> None:
            title = f"Unable to add {show_name}"

            message = f"Could not add {show_name} with {indexer}:{indexer_id}. We were unable to locate the tvdb id at this time."
            if in_list:
                message = f"{in_list.name} with {in_list.indexerid} is already in your show list."

            logger.info(f"{title} {message}")
            ui.notifications.error(title, message)

            return self.redirect("/home/")

        if indexer != "TVDB":
            indexer_id = helpers.tvdbid_from_remote_id(indexer_id, indexer.upper())
            if not indexer_id:
                return add_error()

        existing = Show.find(settings.show_list, indexer_id)
        if try_int(indexer_id) <= 0 or existing:
            return add_error(existing)

        # Trakt-style pick-a-show (#2) confirmation. Search by verified TVDB id (not exact
        # title match); keep the human title in the search box via search_string.
        title = (show_name or "").strip()
        if title:
            return self.redirect(f"/addShows/newShow/?search_string={quote_plus(title)}&indexer_id={quote_plus(str(indexer_id))}")
        return self.redirect(f"/addShows/newShow/?search_string={quote_plus(str(indexer_id))}")

    def addNewShow(self):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        indexer_language = self.get_body_argument("indexerLang", default=settings.INDEXER_DEFAULT_LANGUAGE)

        # grab our list of other dirs if given
        other_shows = self.get_body_arguments("other_shows")
        full_show_path = self.get_body_argument("fullShowPath", default=None)
        root_dir = self.get_body_argument("rootDir", default=None)

        def finishAddShow():
            # if there are no extra shows then go home
            if not other_shows:
                return self.redirect("/home/")

            # peel off the next one
            next_show = other_shows[0]
            remaining_shows = other_shows[1:]

            if not remaining_shows:
                return self.newShow(next_show, [])

            # go to add the next show
            return self.newShow(next_show, remaining_shows)

        # if we're skipping then behave accordingly
        skip_show = self.get_body_argument("skipShow", default=None)
        if skip_show:
            return finishAddShow()

        which_series = self.get_body_argument("whichSeries", default=None)

        # sanity check on our inputs
        if (not root_dir and not full_show_path) or not which_series:
            return _("Missing params, no Indexer ID or folder: {show_to_add} and {root_dir}/{show_path}").format(
                show_to_add=which_series, root_dir=root_dir, show_path=full_show_path
            )

        # figure out what show we're adding and where
        series_pieces = which_series.split("|")
        if (which_series and root_dir) or (which_series and full_show_path and len(series_pieces) > 1):
            if len(series_pieces) < 6:
                logger.error("Unable to add show due to show selection. Not enough arguments: {0}".format((repr(series_pieces))))
                ui.notifications.error(_("Unknown error. Unable to add show due to problem with show selection."))
                return self.redirect("/addShows/existingShows/")

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            # Show name was sent in UTF-8 in the form
            show_name = series_pieces[4]
        else:
            # if no indexer was provided use the default indexer set in General settings
            indexer = int(self.get_body_argument("providedIndexer", default=settings.INDEXER_DEFAULT))
            indexer_id = int(which_series)
            show_name = os.path.basename(os.path.normpath(full_show_path))

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if full_show_path:
            show_dir = os.path.normpath(full_show_path)
            extra_check_dir = show_dir
        else:
            folder_name = show_name
            s = sickchill.indexer.series_by_id(indexerid=indexer_id, indexer=indexer, language=indexer_language)
            if settings.ADD_SHOWS_WITH_YEAR and s.firstAired:
                try:
                    year = "({0})".format(dateutil.parser.parse(s.firstAired).year)
                    if year not in folder_name:
                        folder_name = "{0} {1}".format(s.seriesName, year)
                except (TypeError, ValueError):
                    logger.info(_("Could not append the show year folder for the show: {0}").format(folder_name))

            show_dir = os.path.join(root_dir, sanitize_filename(folder_name))
            extra_check_dir = os.path.join(root_dir, sanitize_filename(show_name))

        # blanket policy - if the dir exists you should have used "add existing show"
        if (os.path.isdir(show_dir) or os.path.isdir(extra_check_dir)) and not full_show_path:
            ui.notifications.error(_("Unable to add show"), _("Folder {show_dir} exists already").format(show_dir=show_dir))
            return self.redirect("/addShows/existingShows/")

        # don't create show dir if config says not to
        if settings.ADD_SHOWS_WO_DIR:
            logger.info(f"Skipping initial creation of {show_dir} due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_dir)
            if not dir_exists:
                logger.exception(f"Unable to create the folder {show_dir}, can't add the show")
                ui.notifications.error(_("Unable to add show"), _("Unable to create the folder {show_dir}, can't add the show").format(show_dir=show_dir))
                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")

            helpers.chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = config.checkbox_to_value(self.get_body_argument("scene", default=None))
        anime = config.checkbox_to_value(self.get_body_argument("anime", default=None))
        season_folders = config.checkbox_to_value(self.get_body_argument("season_folders", default=None))
        subtitles = config.checkbox_to_value(self.get_body_argument("subtitles", default=None))
        subtitles_sc_metadata = config.checkbox_to_value(self.get_body_argument("subtitles_sc_metadata", default=None))

        whitelist = self.get_body_argument("whitelist", default=None)
        blacklist = self.get_body_argument("blacklist", default=None)
        any_qualities = self.get_body_arguments("anyQualities")
        best_qualities = self.get_body_arguments("bestQualities")

        if whitelist:
            whitelist = short_group_names(whitelist)
        else:
            whitelist = []
        if blacklist:
            blacklist = short_group_names(blacklist)
        else:
            blacklist = []

        if not any_qualities:
            any_qualities = []
        if not best_qualities or try_int(self.get_body_argument("quality_preset", default=None)):
            best_qualities = []
        if not isinstance(any_qualities, list):
            any_qualities = [any_qualities]
        if not isinstance(best_qualities, list):
            best_qualities = [best_qualities]
        new_quality = Quality.combineQualities([int(q) for q in any_qualities], [int(q) for q in best_qualities])

        # add the show
        settings.showQueueScheduler.action.add_show(
            indexer,
            indexer_id,
            show_dir=show_dir,
            default_status=int(self.get_body_argument("defaultStatus", default=None)),
            quality=new_quality,
            season_folders=season_folders,
            lang=indexer_language,
            subtitles=subtitles,
            subtitles_sc_metadata=subtitles_sc_metadata,
            anime=anime,
            scene=scene,
            paused=None,
            blacklist=blacklist,
            whitelist=whitelist,
            default_status_after=int(self.get_body_argument("defaultStatusAfter", default=None)),
            root_dir=root_dir,
        )
        ui.notifications.message(_("Show added"), _("Adding the specified show into {show_dir}").format(show_dir=show_dir))

        return finishAddShow()

    @staticmethod
    def split_extra_show(extra_show):
        if not extra_show:
            return None, None, None, None

        split_vals = extra_show.split("|")
        if len(split_vals) == 1:
            indexer = settings.INDEXER_DEFAULT
            show_dir = split_vals[0]
            return indexer, show_dir, None, None
        elif len(split_vals) < 4:
            indexer = split_vals[0]
            show_dir = split_vals[1]
            return indexer, show_dir, None, None

        indexer = split_vals[0]
        show_dir = split_vals[1]
        indexer_id = split_vals[2]
        show_name = "|".join(split_vals[3:])

        return indexer, show_dir, indexer_id, show_name

    def addExistingShows(self):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """

        # grab a list of other shows to add, if provided
        shows_to_add = self.get_arguments("shows_to_add")

        indexer_id_given = []
        dirs_only = []
        # separate all the ones with Indexer IDs
        for cur_dir in shows_to_add:
            if "|" in cur_dir:
                split_vals = cur_dir.split("|")
                if len(split_vals) < 3:
                    dirs_only.append(cur_dir)
            if "|" not in cur_dir:
                dirs_only.append(cur_dir)
            else:
                indexer, show_dir, indexer_id, show_name = self.split_extra_show(cur_dir)

                if not show_dir or not indexer_id or not show_name:
                    continue

                indexer_id_given.append((int(indexer), show_dir, int(indexer_id), show_name))

        # if they want me to prompt for settings then I will just carry on to the newShow page
        if shows_to_add and config.checkbox_to_value(self.get_argument("promptForSettings")):
            return self.newShow(shows_to_add[0], shows_to_add[1:])

        # if they don't want me to prompt for settings then I can just add all the nfo shows now
        num_added = 0
        for cur_show in indexer_id_given:
            indexer, show_dir, indexer_id, show_name = cur_show

            if indexer is not None and indexer_id is not None:
                # add the show
                settings.showQueueScheduler.action.add_show(
                    indexer,
                    indexer_id,
                    show_dir,
                    default_status=settings.STATUS_DEFAULT,
                    quality=settings.QUALITY_DEFAULT,
                    season_folders=settings.SEASON_FOLDERS_DEFAULT,
                    subtitles=settings.SUBTITLES_DEFAULT,
                    anime=settings.ANIME_DEFAULT,
                    scene=settings.SCENE_DEFAULT,
                    default_status_after=settings.STATUS_DEFAULT_AFTER,
                )
                num_added += 1

        if num_added:
            ui.notifications.message(_("Shows Added"), _("Automatically added {num_shows} from their existing metadata files").format(num_shows=str(num_added)))

        # if we're done then go home
        if not dirs_only:
            return self.redirect("/home/")

        # for the remaining shows we need to prompt for each one, so forward this on to the newShow page
        return self.newShow(dirs_only[0], dirs_only[1:])
