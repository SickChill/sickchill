import datetime
import json
import os
import re
import traceback
from operator import itemgetter
from urllib.parse import unquote_plus

import dateutil.parser
from tornado.escape import xhtml_unescape
from tornado.web import HTTPError

import sickchill
from sickchill import logger, settings
from sickchill.helper import sanitize_filename, try_int
from sickchill.oldbeard import config, db, filters, helpers, ui
from sickchill.oldbeard.blackandwhitelist import short_group_names
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.trakt_api import TraktAPI
from sickchill.oldbeard.traktTrending import trakt_trending
from sickchill.show.recommendations.favorites import favorites
from sickchill.show.recommendations.imdb import imdb_popular
from sickchill.show.Show import Show
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home
from sickchill.views.routes import Route


@Route("/addShows(/?.*)", name="addShows")
class AddShows(Home):
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="addShows.mako")
        return t.render(title=_("Add Shows"), header=_("Add Shows"), topmenu="home", controller="addShows", action="index")

    @staticmethod
    def sanitizeFileName(name):
        return sanitize_filename(name)

    def searchIndexersForShowName(self, search_term, lang=None, indexer=None, exact=False):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")
        if not lang or lang == "null":
            lang = settings.INDEXER_DEFAULT_LANGUAGE

        search_term = xhtml_unescape(search_term)

        search_terms = [search_term]

        # If search term ends with what looks like a year, enclose it in ()
        matches = re.match(r"^(.+ |)([12][0-9]{3})$", search_term)
        if matches:
            search_terms.append("{0}({1})".format(matches.group(1), matches.group(2)))

        for term in search_terms:
            # If search term begins with an article, let's also search for it without
            matches = re.match(r"^(?:a|an|the) (.+)$", term, re.I)
            if matches:
                search_terms.append(matches.group(1))

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for index, indexer_object in sickchill.indexer:
            if int(indexer) and int(indexer) != index:
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
            # noinspection PyUnresolvedReferences
            final_results.extend(
                {
                    (
                        sickchill.indexer.name(index),
                        index,
                        indexer_object.show_url,
                        show["id"],
                        show["seriesName"],
                        show["firstAired"],
                        sickchill.tv.Show.find(settings.showList, show["id"]) is not None,
                    )
                    for show in shows
                }
            )

        if exact in [True, "1"]:
            logger.debug(_("Filtering and sorting out excess results because exact match was checked"))
            final_results = [item for item in final_results if search_term.lower() in item[4].lower()]
            final_results.sort(key=itemgetter(4))
            final_results.sort(key=lambda x: x[4].lower().index(search_term.lower()))
            final_results.sort(key=lambda x: x[4].lower() == search_term.lower(), reverse=True)

        lang_id = sickchill.indexer.lang_dict()[lang]
        return json.dumps({"results": final_results, "langid": lang_id, "success": len(final_results) > 0})

    def massAddTable(self, rootDir=None):
        t = PageTemplate(rh=self, filename="home_massAddTable.mako")

        if not rootDir:
            return _("No folders selected.")
        elif not isinstance(rootDir, list):
            root_dirs = [rootDir]
        else:
            root_dirs = rootDir

        root_dirs = [unquote_plus(xhtml_unescape(x)) for x in root_dirs]

        if settings.ROOT_DIRS:
            default_index = int(settings.ROOT_DIRS.split("|")[0])
        else:
            default_index = 0

        if len(root_dirs) > default_index:
            tmp = root_dirs[default_index]
            if tmp in root_dirs:
                root_dirs.remove(tmp)
                root_dirs.insert(0, tmp)

        dir_list = []

        main_db_con = db.DBConnection()
        for root_dir in root_dirs:
            # noinspection PyBroadException
            try:
                file_list = os.listdir(root_dir)
            except Exception:
                continue

            for cur_file in file_list:
                # noinspection PyBroadException
                try:
                    cur_path = os.path.normpath(os.path.join(root_dir, cur_file))
                    if not os.path.isdir(cur_path):
                        continue
                    # ignore Synology folders
                    if cur_file.lower() in ["#recycle", "@eadir"]:
                        continue
                except Exception:
                    continue

                cur_dir = {
                    "dir": cur_path,
                    "existing_info": (None, None, None),
                    "display_dir": "<b>" + os.path.dirname(cur_path) + os.sep + "</b>" + os.path.basename(cur_path),
                }

                # see if the folder is in KODI already
                dirResults = main_db_con.select("SELECT indexer_id FROM tv_shows WHERE location = ? LIMIT 1", [cur_path])

                if dirResults:
                    cur_dir["added_already"] = True
                else:
                    cur_dir["added_already"] = False

                dir_list.append(cur_dir)

                indexer_id = show_name = indexer = None
                for cur_provider in settings.metadata_provider_dict.values():
                    if not (indexer_id and show_name):
                        (indexer_id, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)
                        if all((indexer_id, show_name, indexer)):
                            break

                if all((indexer_id, show_name, indexer)):
                    cur_dir["existing_info"] = (indexer_id, show_name, indexer)

                if indexer_id and Show.find(settings.showList, indexer_id):
                    cur_dir["added_already"] = True
        return t.render(dirList=dir_list)

    def newShow(self, show_to_add=None, other_shows=None, search_string=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, filename="addShows_newShow.mako")

        indexer, show_dir, indexer_id, show_name = self.split_extra_show(show_to_add)

        if indexer_id and indexer and show_name:
            use_provided_info = True
        else:
            use_provided_info = False

        # use the given show_dir for the indexer search if available
        if not show_dir:
            if search_string:
                default_show_name = search_string
            else:
                default_show_name = ""

        elif not show_name:
            default_show_name = re.sub(r" \(\d{4}\)", "", os.path.basename(os.path.normpath(show_dir)).replace(".", " "))
        else:
            default_show_name = show_name

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        provided_indexer_id = int(indexer_id or 0)
        provided_indexer_name = show_name

        provided_indexer = int(indexer or settings.INDEXER_DEFAULT)

        return t.render(
            enable_anime_options=True,
            use_provided_info=use_provided_info,
            default_show_name=default_show_name,
            other_shows=other_shows,
            provided_show_dir=show_dir,
            provided_indexer_id=provided_indexer_id,
            provided_indexer_name=provided_indexer_name,
            provided_indexer=provided_indexer,
            whitelist=[],
            blacklist=[],
            groups=[],
            title=_("New Show"),
            header=_("New Show"),
            topmenu="home",
            controller="addShows",
            action="newShow",
        )

    def trendingShows(self, traktList=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        if not traktList:
            traktList = ""

        traktList = traktList.lower()

        if traktList == "trending":
            page_title = _("Trending Shows")
        elif traktList == "popular":
            page_title = _("Popular Shows")
        elif traktList == "anticipated":
            page_title = _("Most Anticipated Shows")
        elif traktList == "collected":
            page_title = _("Most Collected Shows")
        elif traktList == "watched":
            page_title = _("Most Watched Shows")
        elif traktList == "played":
            page_title = _("Most Played Shows")
        elif traktList == "recommended":
            page_title = _("Recommended Shows")
        elif traktList == "newshow":
            page_title = _("New Shows")
        elif traktList == "newseason":
            page_title = _("Season Premieres")
        else:
            page_title = _("Most Anticipated Shows")

        t = PageTemplate(rh=self, filename="addShows_trendingShows.mako")
        return t.render(title=page_title, header=page_title, enable_anime_options=False, traktList=traktList, controller="addShows", action="trendingShows")

    def getTrendingShows(self, traktList=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and posts them to addNewShow
        """
        t = PageTemplate(rh=self, filename="trendingShows.mako")
        if not traktList:
            traktList = ""

        traktList = traktList.lower()

        if traktList == "trending":
            page_url = "shows/trending"
        elif traktList == "popular":
            page_url = "shows/popular"
        elif traktList == "anticipated":
            page_url = "shows/anticipated"
        elif traktList == "collected":
            page_url = "shows/collected"
        elif traktList == "watched":
            page_url = "shows/watched"
        elif traktList == "played":
            page_url = "shows/played"
        elif traktList == "recommended":
            page_url = "recommendations/shows"
        elif traktList == "newshow":
            page_url = "calendars/all/shows/new/{0}/30".format(datetime.date.today().strftime("%Y-%m-%d"))
        elif traktList == "newseason":
            page_url = "calendars/all/shows/premieres/{0}/30".format(datetime.date.today().strftime("%Y-%m-%d"))
        else:
            page_url = "shows/anticipated"

        trending_shows = []
        black_list = False
        try:
            trending_shows, black_list = trakt_trending.fetch_trending_shows(traktList, page_url)
        except Exception as error:
            logger.warning(f"Could not get trending shows: {error}")

        return t.render(black_list=black_list, trending_shows=trending_shows)

    @staticmethod
    def getTrendingShowImage(indexerId):
        image_url = sickchill.indexer.series_poster_url_by_id(indexerId)
        if image_url:
            image_path = trakt_trending.get_image_path(trakt_trending.get_image_name(indexerId))
            trakt_trending.cache_image(image_url, image_path)
            return indexerId

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        t = PageTemplate(rh=self, filename="addShows_popularShows.mako")
        try:
            popular_shows = imdb_popular.fetch_popular_shows()
            imdb_exception = None
        except Exception as error:
            logger.warning(f"Could not get popular shows: {error}")
            logger.debug(traceback.format_exc())
            popular_shows = None
            imdb_exception = error

        return t.render(
            title=_("Popular Shows"),
            header=_("Popular Shows"),
            popular_shows=popular_shows,
            imdb_exception=imdb_exception,
            imdb_url=imdb_popular.imdb_url,
            topmenu="home",
            controller="addShows",
            action="popularShows",
        )

    def favoriteShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        t = PageTemplate(rh=self, filename="addShows_favoriteShows.mako")
        error = None

        if self.get_body_argument("submit", None):
            tvdb_user = self.get_body_argument("tvdb_user")
            tvdb_user_key = filters.unhide(settings.TVDB_USER_KEY, self.get_body_argument("tvdb_user_key"))
            if tvdb_user and tvdb_user_key:
                if tvdb_user != settings.TVDB_USER or tvdb_user_key != settings.TVDB_USER_KEY:
                    favorites.test_user_key(tvdb_user, tvdb_user_key, 1)

        try:
            favorite_shows = favorites.fetch_indexer_favorites()
        except Exception as error:
            logger.exception(traceback.format_exc())
            logger.warning(_("Could not get favorite shows: {error}").format(error=error))
            favorite_shows = None

        return t.render(
            title=_("Favorite Shows"),
            header=_("Favorite Shows"),
            favorite_shows=favorite_shows,
            favorites_exception=error,
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

    # noinspection PyUnusedLocal
    def addShowByID(
        self,
        indexer_id,
        show_name,
        indexer="TVDB",
        which_series=None,
        indexer_lang=None,
        root_dir=None,
        default_status=None,
        quality_preset=None,
        any_qualities=None,
        best_qualities=None,
        season_folders=None,
        subtitles=None,
        full_show_path=None,
        other_shows=None,
        skip_show=None,
        provided_indexer=None,
        anime=None,
        scene=None,
        blacklist=None,
        whitelist=None,
        default_status_after=None,
        default_season_folders=None,
        configure_show_options=None,
    ):

        if indexer != "TVDB":
            indexer_id = helpers.tvdbid_from_remote_id(indexer_id, indexer.upper())
            if not indexer_id:
                logger.info("Unable to to find tvdb ID to add {0}".format(show_name))
                ui.notifications.error(
                    "Unable to add {0}".format(show_name), "Could not add {0}.  We were unable to locate the tvdb id at this time.".format(show_name)
                )
                return

        indexer_id = try_int(indexer_id)

        if indexer_id <= 0 or Show.find(settings.showList, indexer_id):
            return

        # Sanitize the parameter anyQualities and bestQualities. As these would normally be passed as lists
        any_qualities = any_qualities.split(",") if any_qualities else []
        best_qualities = best_qualities.split(",") if best_qualities else []

        # If configure_show_options is enabled let's use the provided settings
        if config.checkbox_to_value(configure_show_options):
            # prepare the inputs for passing along
            scene = config.checkbox_to_value(scene)
            anime = config.checkbox_to_value(anime)
            season_folders = config.checkbox_to_value(season_folders)
            subtitles = config.checkbox_to_value(subtitles)

            if whitelist:
                whitelist = short_group_names(whitelist)
            if blacklist:
                blacklist = short_group_names(blacklist)

            if not any_qualities:
                any_qualities = []

            if not best_qualities or try_int(quality_preset, None):
                best_qualities = []

            if not isinstance(any_qualities, list):
                any_qualities = [any_qualities]

            if not isinstance(best_qualities, list):
                best_qualities = [best_qualities]

            quality = Quality.combineQualities([int(q) for q in any_qualities], [int(q) for q in best_qualities])

            location = root_dir

        else:
            default_status = settings.STATUS_DEFAULT
            quality = settings.QUALITY_DEFAULT
            season_folders = settings.SEASON_FOLDERS_DEFAULT
            subtitles = settings.SUBTITLES_DEFAULT
            anime = settings.ANIME_DEFAULT
            scene = settings.SCENE_DEFAULT
            default_status_after = settings.STATUS_DEFAULT_AFTER

            if settings.ROOT_DIRS:
                root_dirs = settings.ROOT_DIRS.split("|")
                location = root_dirs[int(root_dirs[0]) + 1]
            else:
                location = None

        if not location:
            logger.info("There was an error creating the show, no root directory setting found")
            return _("No root directories setup, please go back and add one.")

        show_name = sickchill.indexer[1].get_series_by_id(indexer_id, indexer_lang).seriesName
        show_dir = None

        if not show_name:
            ui.notifications.error(_("Unable to add show"))
            return self.redirect("/home/")

        # add the show
        settings.showQueueScheduler.action.add_show(
            indexer=1,
            indexer_id=indexer_id,
            showDir=show_dir,
            default_status=default_status,
            quality=quality,
            season_folders=season_folders,
            lang=indexer_lang,
            subtitles=subtitles,
            subtitles_sr_metadata=None,
            anime=anime,
            scene=scene,
            paused=None,
            blacklist=blacklist,
            whitelist=whitelist,
            default_status_after=default_status_after,
            root_dir=location,
        )

        ui.notifications.message(_("Show added"), _("Adding the specified show {show_name}").format(show_name=show_name))

        # done adding show
        return self.redirect("/home/")

    def addNewShow(
        self,
        whichSeries=None,
        indexerLang=None,
        rootDir=None,
        defaultStatus=None,
        quality_preset=None,
        anyQualities=None,
        bestQualities=None,
        season_folders=None,
        subtitles=None,
        subtitles_sr_metadata=None,
        fullShowPath=None,
        other_shows=None,
        skipShow=None,
        providedIndexer=None,
        anime=None,
        scene=None,
        blacklist=None,
        whitelist=None,
        defaultStatusAfter=None,
    ):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        if not indexerLang:
            indexerLang = settings.INDEXER_DEFAULT_LANGUAGE

        # grab our list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        def finishAddShow():
            # if there are no extra shows then go home
            if not other_shows:
                return self.redirect("/home/")

            # peel off the next one
            next_show_dir = other_shows[0]
            rest_of_show_dirs = other_shows[1:]

            # go to add the next show
            return self.newShow(next_show_dir, rest_of_show_dirs)

        # if we're skipping then behave accordingly
        if skipShow:
            return finishAddShow()

        # sanity check on our inputs
        if (not rootDir and not fullShowPath) or not whichSeries:
            return _("Missing params, no Indexer ID or folder: {show_to_add} and {root_dir}/{show_path}").format(
                show_to_add=whichSeries, root_dir=rootDir, show_path=fullShowPath
            )

        # figure out what show we're adding and where
        series_pieces = whichSeries.split("|")
        if (whichSeries and rootDir) or (whichSeries and fullShowPath and len(series_pieces) > 1):
            if len(series_pieces) < 6:
                logger.error("Unable to add show due to show selection. Not enough arguments: {0}".format((repr(series_pieces))))
                ui.notifications.error(_("Unknown error. Unable to add show due to problem with show selection."))
                return self.redirect("/addShows/existingShows/")

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            # Show name was sent in UTF-8 in the form
            show_name = xhtml_unescape(series_pieces[4])
        else:
            # if no indexer was provided use the default indexer set in General settings
            if not providedIndexer:
                providedIndexer = settings.INDEXER_DEFAULT

            indexer = int(providedIndexer)
            indexer_id = int(whichSeries)
            show_name = os.path.basename(os.path.normpath(xhtml_unescape(fullShowPath)))

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = os.path.normpath(xhtml_unescape(fullShowPath))
            extra_check_dir = show_dir
        else:
            folder_name = show_name
            s = sickchill.indexer.series_by_id(indexerid=indexer_id, indexer=indexer, language=indexerLang)
            if settings.ADD_SHOWS_WITH_YEAR and s.firstAired:
                try:
                    year = "({0})".format(dateutil.parser.parse(s.firstAired).year)
                    if year not in folder_name:
                        folder_name = "{0} {1}".format(s.seriesName, year)
                except (TypeError, ValueError):
                    logger.info(_("Could not append the show year folder for the show: {0}").format(folder_name))

            show_dir = os.path.join(rootDir, sanitize_filename(xhtml_unescape(folder_name)))
            extra_check_dir = os.path.join(rootDir, sanitize_filename(xhtml_unescape(show_name)))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if (os.path.isdir(show_dir) or os.path.isdir(extra_check_dir)) and not fullShowPath:
            ui.notifications.error(_("Unable to add show"), _("Folder {show_dir} exists already").format(show_dir=show_dir))
            return self.redirect("/addShows/existingShows/")

        # don't create show dir if config says not to
        if settings.ADD_SHOWS_WO_DIR:
            logger.info("Skipping initial creation of " + show_dir + " due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_dir)
            if not dir_exists:
                logger.exception("Unable to create the folder " + show_dir + ", can't add the show")
                ui.notifications.error(_("Unable to add show"), _("Unable to create the folder {show_dir}, can't add the show").format(show_dir=show_dir))
                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                helpers.chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = config.checkbox_to_value(scene)
        anime = config.checkbox_to_value(anime)
        season_folders = config.checkbox_to_value(season_folders)
        subtitles = config.checkbox_to_value(subtitles)
        subtitles_sr_metadata = config.checkbox_to_value(subtitles_sr_metadata)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        if not anyQualities:
            anyQualities = []
        if not bestQualities or try_int(quality_preset, None):
            bestQualities = []
        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]
        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]
        newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])

        # add the show
        settings.showQueueScheduler.action.add_show(
            indexer,
            indexer_id,
            showDir=show_dir,
            default_status=int(defaultStatus),
            quality=newQuality,
            season_folders=season_folders,
            lang=indexerLang,
            subtitles=subtitles,
            subtitles_sr_metadata=subtitles_sr_metadata,
            anime=anime,
            scene=scene,
            paused=None,
            blacklist=blacklist,
            whitelist=whitelist,
            default_status_after=int(defaultStatusAfter),
            root_dir=rootDir,
        )
        ui.notifications.message(_("Show added"), _("Adding the specified show into {show_dir}").format(show_dir=show_dir))

        return finishAddShow()

    @staticmethod
    def split_extra_show(extra_show):
        if not extra_show:
            return None, None, None, None
        split_vals = extra_show.split("|")
        if len(split_vals) < 4:
            indexer = split_vals[0]
            show_dir = split_vals[1]
            return indexer, show_dir, None, None
        indexer = split_vals[0]
        show_dir = split_vals[1]
        indexer_id = split_vals[2]
        show_name = "|".join(split_vals[3:])

        return indexer, show_dir, indexer_id, show_name

    def addExistingShows(self, shows_to_add, promptForSettings, **kwargs):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """

        # grab a list of other shows to add, if provided
        if not shows_to_add:
            shows_to_add = []
        elif not isinstance(shows_to_add, list):
            shows_to_add = [shows_to_add]

        shows_to_add = [unquote_plus(xhtml_unescape(x)) for x in shows_to_add]

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
        if shows_to_add and config.checkbox_to_value(promptForSettings):
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
