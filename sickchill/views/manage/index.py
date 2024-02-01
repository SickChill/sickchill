import json
import ntpath
import os
import posixpath

from sickchill import logger, settings
from sickchill.helper import episode_num, try_int
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException
from sickchill.oldbeard import db, subtitles as subtitle_module, ui
from sickchill.oldbeard.common import Overview, Quality, SNATCHED
from sickchill.show.Show import Show
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home, WebRoot
from sickchill.views.routes import Route


@Route("/manage(/?.*)", name="manage:main")
class Manage(Home, WebRoot):
    def index(self):
        t = PageTemplate(rh=self, filename="manage.mako")
        return t.render(title=_("Mass Update"), header=_("Mass Update"), topmenu="manage", controller="manage", action="index")

    @staticmethod
    def showEpisodeStatuses(indexer_id, whichStatus):
        status_list = [int(whichStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        main_db_con = db.DBConnection()
        cur_show_results = main_db_con.select(
            "SELECT season, episode, name FROM tv_episodes WHERE showid = ? AND season != 0 AND status IN ({0})".format(",".join(["?"] * len(status_list))),
            [int(indexer_id)] + status_list,
        )

        result = {}
        for cur_result in cur_show_results:
            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = cur_result["name"]

        return json.dumps(result)

    def episodeStatuses(self):
        which_status = self.get_query_argument("whichStatus", None)
        if which_status:
            status_list = [int(which_status)]
            if status_list[0] == SNATCHED:
                status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST
        else:
            status_list = []

        t = PageTemplate(rh=self, filename="manage_episodeStatuses.mako")

        # if we have no status then this is as far as we need to go
        if not status_list:
            return t.render(
                title=_("Episode Overview"),
                header=_("Episode Overview"),
                topmenu="manage",
                show_names=None,
                whichStatus=which_status,
                ep_counts=None,
                sorted_show_ids=None,
                controller="manage",
                action="episodeStatuses",
            )

        main_db_con = db.DBConnection()
        status_results = main_db_con.select(
            "SELECT show_name, tv_shows.indexer_id AS indexer_id FROM tv_episodes, tv_shows WHERE tv_episodes.status IN ({0}) AND season != 0 AND "
            "tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name".format(",".join(["?"] * len(status_list))),
            status_list,
        )

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            cur_indexer_id = int(cur_status_result["indexer_id"])
            if cur_indexer_id not in ep_counts:
                ep_counts[cur_indexer_id] = 1
            else:
                ep_counts[cur_indexer_id] += 1

            show_names[cur_indexer_id] = cur_status_result["show_name"]
            if cur_indexer_id not in sorted_show_ids:
                sorted_show_ids.append(cur_indexer_id)

        return t.render(
            title=_("Episode Overview"),
            header=_("Episode Overview"),
            topmenu="manage",
            whichStatus=which_status,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            controller="manage",
            action="episodeStatuses",
        )

    # noinspection PyUnusedLocal
    def changeEpisodeStatuses(self, oldStatus, newStatus, *args, **kwargs):
        status_list = [int(oldStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        to_change = {}
        self.to_change_show = []
        self.to_change_eps = []

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split("-")

            # we don't care about unchecked checkboxes
            if kwargs[arg] != "on":
                continue

            if indexer_id not in to_change:
                to_change[indexer_id] = []

            to_change[indexer_id].append(what)

        main_db_con = db.DBConnection()
        for cur_indexer_id in to_change:
            self.to_change_show = cur_indexer_id
            # get a list of all the eps we want to change if they just said "all"
            if "all" in to_change[cur_indexer_id]:
                all_eps_results = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN ({0}) AND season != 0 AND showid = ?".format(",".join(["?"] * len(status_list))),
                    status_list + [cur_indexer_id],
                )
                all_eps = [str(x["season"]) + "x" + str(x["episode"]) for x in all_eps_results]
                self.to_change_eps = all_eps
            else:
                self.to_change_eps = to_change[cur_indexer_id]

            self.setStatus(direct=True)

        return self.redirect("/manage/episodeStatuses/")

    @staticmethod
    def showSubtitleMissed(indexer_id, whichSubs):
        main_db_con = db.DBConnection()
        cur_show_results = main_db_con.select(
            "SELECT season, episode, name, subtitles FROM tv_episodes WHERE showid = ? {0} AND (status LIKE '%4' OR status LIKE '%6') and "
            "location != ''".format(("AND season != 0 ", "")[settings.SUBTITLES_INCLUDE_SPECIALS]),
            [int(indexer_id)],
        )
        result = {}
        for cur_result in cur_show_results:
            if whichSubs == "all":
                if not frozenset(subtitle_module.wanted_languages()).difference(cur_result["subtitles"].split(",")):
                    continue
            elif whichSubs in cur_result["subtitles"]:
                continue

            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode]["name"] = cur_result["name"]

            result[cur_season][cur_episode]["subtitles"] = cur_result["subtitles"]

        return json.dumps(result)

    def subtitleMissed(self):
        which_subs = self.get_body_argument("whichSubs", None)
        t = PageTemplate(rh=self, filename="manage_subtitleMissed.mako")

        if not which_subs:
            return t.render(
                whichSubs=which_subs,
                title=_("Episode Overview"),
                header=_("Episode Overview"),
                topmenu="manage",
                show_names=None,
                ep_counts=None,
                sorted_show_ids=None,
                controller="manage",
                action="subtitleMissed",
            )

        main_db_con = db.DBConnection()
        status_results = main_db_con.select(
            "SELECT show_name, tv_shows.indexer_id as indexer_id, tv_episodes.subtitles subtitles "
            + "FROM tv_episodes, tv_shows "
            + "WHERE tv_shows.subtitles = 1 AND (tv_episodes.status LIKE '%4' OR tv_episodes.status LIKE '%6') AND tv_episodes.season != 0 "
            + "AND tv_episodes.location != '' AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name"
        )

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            if which_subs == "all":
                if not frozenset(subtitle_module.wanted_languages()).difference(cur_status_result["subtitles"].split(",")):
                    continue
            elif which_subs in cur_status_result["subtitles"]:
                continue

            cur_indexer_id = int(cur_status_result["indexer_id"])
            if cur_indexer_id not in ep_counts:
                ep_counts[cur_indexer_id] = 1
            else:
                ep_counts[cur_indexer_id] += 1

            show_names[cur_indexer_id] = cur_status_result["show_name"]
            if cur_indexer_id not in sorted_show_ids:
                sorted_show_ids.append(cur_indexer_id)

        return t.render(
            whichSubs=which_subs,
            show_names=show_names,
            ep_counts=ep_counts,
            sorted_show_ids=sorted_show_ids,
            title=_("Missing Subtitles"),
            header=_("Missing Subtitles"),
            topmenu="manage",
            controller="manage",
            action="subtitleMissed",
        )

    # noinspection PyUnusedLocal
    def downloadSubtitleMissed(self, *args, **kwargs):
        to_download = {}

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split("-")

            # we don't care about unchecked checkboxes
            if kwargs[arg] != "on":
                continue

            if indexer_id not in to_download:
                to_download[indexer_id] = []

            to_download[indexer_id].append(what)

        for cur_indexer_id in to_download:
            # get a list of all the eps we want to download subtitles if they just said "all"
            if "all" in to_download[cur_indexer_id]:
                main_db_con = db.DBConnection()
                all_eps_results = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE (status LIKE '%4' OR status LIKE '%6') {0} AND showid = ? AND location != ''".format(
                        ("AND season != 0 ", "")[settings.SUBTITLES_INCLUDE_SPECIALS]
                    ),
                    [cur_indexer_id],
                )
                to_download[cur_indexer_id] = [str(x["season"]) + "x" + str(x["episode"]) for x in all_eps_results]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split("x")

                show = Show.find(settings.showList, int(cur_indexer_id))
                show.getEpisode(season, episode).download_subtitles()

        return self.redirect("/manage/subtitleMissed/")

    def backlogShow(self, indexer_id):
        show_object = Show.find(settings.showList, int(indexer_id))

        if show_object:
            settings.backlogSearchScheduler.action.searchBacklog([show_object])

        return self.redirect("/manage/backlogOverview/")

    def backlogOverview(self):
        t = PageTemplate(rh=self, filename="manage_backlogOverview.mako")

        showCounts = {}
        showCats = {}
        showSQLResults = {}

        main_db_con = db.DBConnection()
        for current_show in settings.showList:
            epCounts = {
                Overview.SKIPPED: 0,
                Overview.WANTED: 0,
                Overview.QUAL: 0,
                Overview.GOOD: 0,
                Overview.UNAIRED: 0,
                Overview.SNATCHED: 0,
                Overview.SNATCHED_PROPER: 0,
                Overview.SNATCHED_BEST: 0,
            }
            epCats = {}

            sql_results = main_db_con.select(
                "SELECT status, season, episode, name, airdate FROM tv_episodes WHERE tv_episodes.season IS NOT NULL "
                "AND tv_episodes.showid IN (SELECT tv_shows.indexer_id FROM tv_shows WHERE tv_shows.indexer_id = ? "
                "AND paused = 0) ORDER BY tv_episodes.season DESC, tv_episodes.episode DESC",
                [current_show.indexerid],
            )

            for curResult in sql_results:
                curEpCat = current_show.getOverview(curResult["status"], backlog=settings.BACKLOG_MISSING_ONLY)
                if curEpCat:
                    epCats["{ep}".format(ep=episode_num(curResult["season"], curResult["episode"]))] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[current_show.indexerid] = epCounts
            showCats[current_show.indexerid] = epCats
            showSQLResults[current_show.indexerid] = sql_results

        def showQualSnatched(show):
            return Quality.splitQuality(show.quality)[1]

        totalWanted = totalQual = totalQualSnatched = 0
        backLogShows = sorted(
            [
                x
                for x in settings.showList
                if (
                    showCounts[x.indexerid][Overview.QUAL]
                    or showCounts[x.indexerid][Overview.WANTED]
                    or (0, showCounts[x.indexerid][Overview.SNATCHED])[len(showQualSnatched(x)) > 0]
                )
            ],
            key=lambda x: x.sort_name,
        )
        for current_show in backLogShows:
            totalWanted += showCounts[current_show.indexerid][Overview.WANTED]
            totalQual += showCounts[current_show.indexerid][Overview.QUAL]
            if showQualSnatched(current_show):
                totalQualSnatched += showCounts[current_show.indexerid][Overview.SNATCHED]

        return t.render(
            showCounts=showCounts,
            showCats=showCats,
            totalQual=totalQual,
            showQualSnatched=showQualSnatched,
            totalWanted=totalWanted,
            totalQualSnatched=totalQualSnatched,
            backLogShows=backLogShows,
            showSQLResults=showSQLResults,
            controller="manage",
            action="backlogOverview",
            title=_("Backlog Overview"),
            header=_("Backlog Overview"),
            topmenu="manage",
        )

    @staticmethod
    def __gooey_path(name, method):
        result = getattr(os.path, method)(name)
        if result == name or not result:
            result = getattr(ntpath, method)(name)
            if result == name or not result:
                result = getattr(posixpath, method)(name)

        return result

    # noinspection PyProtectedMember
    def massEdit(self):
        t = PageTemplate(rh=self, filename="manage_massEdit.mako")

        edit = self.get_body_arguments("edit")

        show_list = []
        show_names = []
        for show_id in edit:
            show_object = Show.find(settings.showList, show_id)
            if show_object:
                show_list.append(show_object)
                show_names.append(show_object.name)

        season_folders_all_same = True
        last_season_folders = None

        paused_all_same = True
        last_paused = None

        default_ep_status_all_same = True
        last_default_ep_status = None

        anime_all_same = True
        last_anime = None

        sports_all_same = True
        last_sports = None

        quality_all_same = True
        last_quality = None

        subtitles_all_same = True
        last_subtitles = None

        scene_all_same = True
        last_scene = None

        air_by_date_all_same = True
        last_air_by_date = None

        root_dir_list = []

        for current_show in show_list:
            show_root_dir = self.__gooey_path(current_show._location, "dirname")
            if show_root_dir and show_root_dir != current_show._location and show_root_dir not in root_dir_list:
                root_dir_list.append(show_root_dir)

            # if we know they're not all the same then no point even bothering
            if paused_all_same:
                # if we had a value already and this value is different, then they're not all the same
                if last_paused not in (None, current_show.paused):
                    paused_all_same = False
                else:
                    last_paused = current_show.paused

            if default_ep_status_all_same:
                if last_default_ep_status not in (None, current_show.default_ep_status):
                    default_ep_status_all_same = False
                else:
                    last_default_ep_status = current_show.default_ep_status

            if anime_all_same:
                # if we had a value already and this value is different, then they're not all the same
                if last_anime not in (None, current_show.is_anime):
                    anime_all_same = False
                else:
                    last_anime = current_show.anime

            if season_folders_all_same:
                if last_season_folders not in (None, current_show.season_folders):
                    season_folders_all_same = False
                else:
                    last_season_folders = current_show.season_folders

            if quality_all_same:
                if last_quality not in (None, current_show.quality):
                    quality_all_same = False
                else:
                    last_quality = current_show.quality

            if subtitles_all_same:
                if last_subtitles not in (None, current_show.subtitles):
                    subtitles_all_same = False
                else:
                    last_subtitles = current_show.subtitles

            if scene_all_same:
                if last_scene not in (None, current_show.scene):
                    scene_all_same = False
                else:
                    last_scene = current_show.scene

            if sports_all_same:
                if last_sports not in (None, current_show.sports):
                    sports_all_same = False
                else:
                    last_sports = current_show.sports

            if air_by_date_all_same:
                if last_air_by_date not in (None, current_show.air_by_date):
                    air_by_date_all_same = False
                else:
                    last_air_by_date = current_show.air_by_date

        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        anime_value = last_anime if anime_all_same else None
        season_folders_value = last_season_folders if season_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        scene_value = last_scene if scene_all_same else None
        sports_value = last_sports if sports_all_same else None
        air_by_date_value = last_air_by_date if air_by_date_all_same else None
        ignore_words_value = None
        prefer_words_value = None
        require_words_value = None

        return t.render(
            edit_list=edit,
            show_names=show_names,
            default_ep_status_value=default_ep_status_value,
            paused_value=paused_value,
            anime_value=anime_value,
            season_folders_value=season_folders_value,
            quality_value=quality_value,
            subtitles_value=subtitles_value,
            scene_value=scene_value,
            sports_value=sports_value,
            air_by_date_value=air_by_date_value,
            root_dir_list=root_dir_list,
            title=_("Mass Edit"),
            header=_("Mass Edit"),
            controller="manage",
            action="massEdit",
            topmenu="manage",
            ignore_words_value=ignore_words_value,
            prefer_words_value=prefer_words_value,
            require_words_value=require_words_value,
        )

    # noinspection PyProtectedMember, PyUnusedLocal
    def massEditSubmit(self):
        paused = self.get_body_argument("paused", None)
        default_ep_status = self.get_body_argument("default_ep_status", None)
        anime = self.get_body_argument("anime", None)
        sports = self.get_body_argument("sports", None)
        scene = self.get_body_argument("scene", None)
        season_folders = self.get_body_argument("season_folders", None)
        quality_preset = self.get_body_argument("quality_preset", None)
        subtitles = self.get_body_argument("subtitles", None)
        air_by_date = self.get_body_argument("air_by_date", None)
        any_qualities = self.get_body_arguments("anyQualities")
        best_qualities = self.get_body_arguments("bestQualities")
        edit = self.get_body_arguments("edit")
        mass_ignore_words = self.get_body_argument("mass_ignore_words", None)
        mass_prefer_words = self.get_body_argument("mass_prefer_words", None)
        mass_require_words = self.get_body_argument("mass_require_words", None)
        ignore_words = self.get_body_argument("ignore_words", None)
        prefer_words = self.get_body_argument("prefer_words", None)
        require_words = self.get_body_argument("require_words", None)

        root_dir_map = {}
        for root_dir in [x for x in self.request.body_arguments if x.startswith("orig_root_dir_")]:
            old_root = self.get_body_argument(root_dir, None)
            new_root = self.get_body_argument(root_dir.replace("orig_root_dir_", "new_root_dir_"), None)
            if old_root is not None and new_root is not None:
                root_dir_map[old_root] = new_root

        errors = []
        for current_show in edit:
            current_show_errors = []
            show_object = Show.find(settings.showList, current_show)
            if not show_object:
                continue

            show_root_dir = self.__gooey_path(show_object._location, "dirname")
            cur_show_dir = self.__gooey_path(show_object._location, "basename")
            if show_root_dir and root_dir_map.get(show_root_dir) and show_root_dir != root_dir_map.get(show_root_dir):
                new_show_dir = os.path.join(root_dir_map[show_root_dir], cur_show_dir)
                logger.info(f"For show {show_object.name} changing dir from {show_object._location} to {new_show_dir}")
            else:
                new_show_dir = show_object._location

            new_paused = ("off", "on")[(paused == "enable", show_object.paused)[paused == "keep"]]
            new_default_ep_status = (default_ep_status, show_object.default_ep_status)[default_ep_status == "keep"]
            new_anime = ("off", "on")[(anime == "enable", show_object.anime)[anime == "keep"]]
            new_sports = ("off", "on")[(sports == "enable", show_object.sports)[sports == "keep"]]
            new_scene = ("off", "on")[(scene == "enable", show_object.scene)[scene == "keep"]]
            new_air_by_date = ("off", "on")[(air_by_date == "enable", show_object.air_by_date)[air_by_date == "keep"]]
            new_season_folders = ("off", "on")[(season_folders == "enable", show_object.season_folders)[season_folders == "keep"]]
            new_subtitles = ("off", "on")[(subtitles == "enable", show_object.subtitles)[subtitles == "keep"]]

            # new mass words update section
            if ignore_words == "new":
                new_ignore_words = mass_ignore_words
            elif ignore_words == "clear":
                new_ignore_words = ""
            else:
                new_ignore_words = show_object.rls_ignore_words

            if require_words == "new":
                new_require_words = mass_require_words
            elif require_words == "clear":
                new_require_words = ""
            else:
                new_require_words = show_object.rls_require_words

            if prefer_words == "new":
                new_prefer_words = mass_prefer_words
            elif prefer_words == "clear":
                new_prefer_words = ""
            else:
                new_prefer_words = show_object.rls_prefer_words

            if quality_preset == "keep":
                any_qualities, best_qualities = Quality.splitQuality(show_object.quality)
            elif try_int(quality_preset, None):
                best_qualities = []

            exceptions_list = []

            current_show_errors += self.editShow(
                current_show,
                new_show_dir,
                any_qualities,
                best_qualities,
                exceptions_list,
                defaultEpStatus=new_default_ep_status,
                season_folders=new_season_folders,
                paused=new_paused,
                sports=new_sports,
                subtitles=new_subtitles,
                rls_ignore_words=new_ignore_words,
                rls_prefer_words=new_prefer_words,
                rls_require_words=new_require_words,
                anime=new_anime,
                scene=new_scene,
                air_by_date=new_air_by_date,
                directCall=True,
            )

            if current_show_errors:
                logger.exception(f"Errors: {current_show_errors}")
                errors.append(f"<b>{show_object.name}:</b>\n<ul>" + " ".join([f"<li>{error}</li>" for error in current_show_errors]) + "</ul>")

        if errors:
            ui.notifications.error(
                _("{num_errors:d} error{plural} while saving changes:").format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"), " ".join(errors)
            )

        return self.redirect("/manage/")

    def massUpdate(self):
        update = self.get_body_arguments("update")
        refresh = self.get_body_arguments("refresh")
        rename = self.get_body_arguments("rename")
        subtitle = self.get_body_arguments("subtitle")
        delete = self.get_body_arguments("delete")
        remove = self.get_body_arguments("remove")
        metadata = self.get_body_arguments("metadata")
        edit = self.get_body_arguments("edit")

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(update + refresh + rename + subtitle + delete + remove + metadata):
            if curShowID == "":
                continue

            show_object = Show.find(settings.showList, int(curShowID))
            if not show_object:
                continue

            if curShowID in delete:
                settings.showQueueScheduler.action.remove_show(show_object, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in remove:
                settings.showQueueScheduler.action.remove_show(show_object)
                # don't do anything else if it's being removed
                continue

            if curShowID in update:
                try:
                    settings.showQueueScheduler.action.update_show(show_object, True)
                    updates.append(show_object.name)
                except CantUpdateShowException as error:
                    errors.append(_("Unable to update show: {exception_format}").format(exception_format=error))

            # don't bother refreshing shows that were updated anyway
            if curShowID in refresh and curShowID not in update:
                try:
                    settings.showQueueScheduler.action.refresh_show(show_object, force=True)
                    refreshes.append(show_object.name)
                except CantRefreshShowException as error:
                    errors.append(_("Unable to refresh show {show_name}: {exception_format}").format(show_name=show_object.name, exception_format=error))

            if curShowID in rename:
                settings.showQueueScheduler.action.rename_show_episodes(show_object)
                renames.append(show_object.name)

            if curShowID in subtitle:
                settings.showQueueScheduler.action.download_subtitles(show_object)
                subtitles.append(show_object.name)

        if errors:
            ui.notifications.error(_("Errors encountered"), "<br >\n".join(errors))

        message_detail = ""

        if updates:
            message_detail += "<br><b>" + _("Updates") + "</b><br><ul><li>"
            message_detail += "</li><li>".join(updates)
            message_detail += "</li></ul>"

        if refreshes:
            message_detail += "<br><b>" + _("Refreshes") + "</b><br><ul><li>"
            message_detail += "</li><li>".join(refreshes)
            message_detail += "</li></ul>"

        if renames:
            message_detail += "<br><b>" + _("Renames") + "</b><br><ul><li>"
            message_detail += "</li><li>".join(renames)
            message_detail += "</li></ul>"

        if subtitles:
            message_detail += "<br><b>" + _("Subtitles") + "</b><br><ul><li>"
            message_detail += "</li><li>".join(subtitles)
            message_detail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            ui.notifications.message(_("The following actions were queued") + ":", message_detail)

        if edit:
            return self.massEdit()

        return self.redirect("/manage/")

    def failedDownloads(self):
        remove = self.get_body_arguments("remove")
        limit = self.get_argument("limit", "100")
        failed_db_con = db.DBConnection("failed.db")

        if limit == "0":
            sql_results = failed_db_con.select("SELECT * FROM failed")
        else:
            sql_results = failed_db_con.select("SELECT * FROM failed LIMIT ?", [limit])

        for release in remove:
            failed_db_con.action("DELETE FROM failed WHERE failed.release = ?", [release])

        if remove:
            return self.redirect("/manage/failedDownloads/")

        t = PageTemplate(rh=self, filename="manage_failedDownloads.mako")

        return t.render(
            limit=limit,
            failedResults=sql_results,
            title=_("Failed Downloads"),
            header=_("Failed Downloads"),
            topmenu="manage",
            controller="manage",
            action="failedDownloads",
        )
