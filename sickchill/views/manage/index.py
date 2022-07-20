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
    def index(self, *args, **kwargs):
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

    def episodeStatuses(self, whichStatus=None):
        if whichStatus:
            status_list = [int(whichStatus)]
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
                whichStatus=whichStatus,
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
            whichStatus=whichStatus,
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

            # get a list of all the eps we want to change if they just said "all"
            if "all" in to_change[cur_indexer_id]:
                all_eps_results = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN ({0}) AND season != 0 AND showid = ?".format(",".join(["?"] * len(status_list))),
                    status_list + [cur_indexer_id],
                )
                all_eps = [str(x["season"]) + "x" + str(x["episode"]) for x in all_eps_results]
                to_change[cur_indexer_id] = all_eps

            self.setStatus(cur_indexer_id, "|".join(to_change[cur_indexer_id]), newStatus, direct=True)

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

    def subtitleMissed(self, whichSubs=None):
        t = PageTemplate(rh=self, filename="manage_subtitleMissed.mako")

        if not whichSubs:
            return t.render(
                whichSubs=whichSubs,
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
            if whichSubs == "all":
                if not frozenset(subtitle_module.wanted_languages()).difference(cur_status_result["subtitles"].split(",")):
                    continue
            elif whichSubs in cur_status_result["subtitles"]:
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
            whichSubs=whichSubs,
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
        show_obj = Show.find(settings.showList, int(indexer_id))

        if show_obj:
            settings.backlogSearchScheduler.action.searchBacklog([show_obj])

        return self.redirect("/manage/backlogOverview/")

    def backlogOverview(self):
        t = PageTemplate(rh=self, filename="manage_backlogOverview.mako")

        showCounts = {}
        showCats = {}
        showSQLResults = {}

        main_db_con = db.DBConnection()
        for curShow in settings.showList:

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
                [curShow.indexerid],
            )

            for curResult in sql_results:
                curEpCat = curShow.getOverview(curResult["status"], backlog=settings.BACKLOG_MISSING_ONLY)
                if curEpCat:

                    epCats["{ep}".format(ep=episode_num(curResult["season"], curResult["episode"]))] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats
            showSQLResults[curShow.indexerid] = sql_results

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
        for curShow in backLogShows:
            totalWanted += showCounts[curShow.indexerid][Overview.WANTED]
            totalQual += showCounts[curShow.indexerid][Overview.QUAL]
            if showQualSnatched(curShow):
                totalQualSnatched += showCounts[curShow.indexerid][Overview.SNATCHED]

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
    def massEdit(self, toEdit=None):
        t = PageTemplate(rh=self, filename="manage_massEdit.mako")

        if not toEdit:
            return self.redirect("/manage/")

        showIDs = toEdit.split("|")
        showList = []
        showNames = []
        for curID in showIDs:
            curID = int(curID)
            show_obj = Show.find(settings.showList, curID)
            if show_obj:
                showList.append(show_obj)
                showNames.append(show_obj.name)

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

        for curShow in showList:

            cur_root_dir = self.__gooey_path(curShow._location, "dirname")
            if cur_root_dir and cur_root_dir != curShow._location and cur_root_dir not in root_dir_list:
                root_dir_list.append(cur_root_dir)

            # if we know they're not all the same then no point even bothering
            if paused_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_paused not in (None, curShow.paused):
                    paused_all_same = False
                else:
                    last_paused = curShow.paused

            if default_ep_status_all_same:
                if last_default_ep_status not in (None, curShow.default_ep_status):
                    default_ep_status_all_same = False
                else:
                    last_default_ep_status = curShow.default_ep_status

            if anime_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_anime not in (None, curShow.is_anime):
                    anime_all_same = False
                else:
                    last_anime = curShow.anime

            if season_folders_all_same:
                if last_season_folders not in (None, curShow.season_folders):
                    season_folders_all_same = False
                else:
                    last_season_folders = curShow.season_folders

            if quality_all_same:
                if last_quality not in (None, curShow.quality):
                    quality_all_same = False
                else:
                    last_quality = curShow.quality

            if subtitles_all_same:
                if last_subtitles not in (None, curShow.subtitles):
                    subtitles_all_same = False
                else:
                    last_subtitles = curShow.subtitles

            if scene_all_same:
                if last_scene not in (None, curShow.scene):
                    scene_all_same = False
                else:
                    last_scene = curShow.scene

            if sports_all_same:
                if last_sports not in (None, curShow.sports):
                    sports_all_same = False
                else:
                    last_sports = curShow.sports

            if air_by_date_all_same:
                if last_air_by_date not in (None, curShow.air_by_date):
                    air_by_date_all_same = False
                else:
                    last_air_by_date = curShow.air_by_date

        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        anime_value = last_anime if anime_all_same else None
        season_folders_value = last_season_folders if season_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        scene_value = last_scene if scene_all_same else None
        sports_value = last_sports if sports_all_same else None
        air_by_date_value = last_air_by_date if air_by_date_all_same else None

        return t.render(
            showList=toEdit,
            showNames=showNames,
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
        )

    # noinspection PyProtectedMember, PyUnusedLocal
    def massEditSubmit(
        self,
        paused=None,
        default_ep_status=None,
        anime=None,
        sports=None,
        scene=None,
        season_folders=None,
        quality_preset=None,
        subtitles=None,
        air_by_date=None,
        anyQualities=None,
        bestQualities=None,
        toEdit=None,
        *args,
        **kwargs,
    ):
        dir_map = {}
        for cur_arg in [x for x in kwargs if x.startswith("orig_root_dir_")]:
            dir_map[kwargs[cur_arg]] = kwargs[cur_arg.replace("orig_root_dir_", "new_root_dir_")]

        showIDs = toEdit.split("|")
        errors = []
        for curShow in showIDs:
            curErrors = []
            show_obj = Show.find(settings.showList, int(curShow or 0))
            if not show_obj:
                continue

            cur_root_dir = self.__gooey_path(show_obj._location, "dirname")
            cur_show_dir = self.__gooey_path(show_obj._location, "basename")
            if cur_root_dir and dir_map.get(cur_root_dir) and cur_root_dir != dir_map.get(cur_root_dir):
                new_show_dir = os.path.join(dir_map[cur_root_dir], cur_show_dir)
                logger.info("For show " + show_obj.name + " changing dir from " + show_obj._location + " to " + new_show_dir)
            else:
                new_show_dir = show_obj._location

            new_paused = ("off", "on")[(paused == "enable", show_obj.paused)[paused == "keep"]]
            new_default_ep_status = (default_ep_status, show_obj.default_ep_status)[default_ep_status == "keep"]
            new_anime = ("off", "on")[(anime == "enable", show_obj.anime)[anime == "keep"]]
            new_sports = ("off", "on")[(sports == "enable", show_obj.sports)[sports == "keep"]]
            new_scene = ("off", "on")[(scene == "enable", show_obj.scene)[scene == "keep"]]
            new_air_by_date = ("off", "on")[(air_by_date == "enable", show_obj.air_by_date)[air_by_date == "keep"]]
            new_season_folders = ("off", "on")[(season_folders == "enable", show_obj.season_folders)[season_folders == "keep"]]
            new_subtitles = ("off", "on")[(subtitles == "enable", show_obj.subtitles)[subtitles == "keep"]]

            if quality_preset == "keep":
                anyQualities, bestQualities = Quality.splitQuality(show_obj.quality)
            elif try_int(quality_preset, None):
                bestQualities = []

            exceptions_list = []

            curErrors += self.editShow(
                curShow,
                new_show_dir,
                anyQualities,
                bestQualities,
                exceptions_list,
                defaultEpStatus=new_default_ep_status,
                season_folders=new_season_folders,
                paused=new_paused,
                sports=new_sports,
                subtitles=new_subtitles,
                anime=new_anime,
                scene=new_scene,
                air_by_date=new_air_by_date,
                directCall=True,
            )

            if curErrors:
                logger.exception("Errors: " + str(curErrors))
                errors.append("<b>{0}:</b>\n<ul>".format(show_obj.name) + " ".join(["<li>{0}</li>".format(error) for error in curErrors]) + "</ul>")

        if errors:
            ui.notifications.error(
                _("{num_errors:d} error{plural} while saving changes:").format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"), " ".join(errors)
            )

        return self.redirect("/manage/")

    def massUpdate(self, toUpdate=None, toRefresh=None, toRename=None, toDelete=None, toRemove=None, toMetadata=None, toSubtitle=None):

        toUpdate = toUpdate.split("|") if toUpdate else []
        toRefresh = toRefresh.split("|") if toRefresh else []
        toRename = toRename.split("|") if toRename else []
        toSubtitle = toSubtitle.split("|") if toSubtitle else []
        toDelete = toDelete.split("|") if toDelete else []
        toRemove = toRemove.split("|") if toRemove else []
        toMetadata = toMetadata.split("|") if toMetadata else []

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(toUpdate + toRefresh + toRename + toSubtitle + toDelete + toRemove + toMetadata):

            if curShowID == "":
                continue

            show_obj = Show.find(settings.showList, int(curShowID))
            if not show_obj:
                continue

            if curShowID in toDelete:
                settings.showQueueScheduler.action.remove_show(show_obj, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in toRemove:
                settings.showQueueScheduler.action.remove_show(show_obj)
                # don't do anything else if it's being remove
                continue

            if curShowID in toUpdate:
                try:
                    settings.showQueueScheduler.action.update_show(show_obj, True)
                    updates.append(show_obj.name)
                except CantUpdateShowException as e:
                    errors.append(_("Unable to update show: {exception_format}").format(exception_format=e))

            # don't bother refreshing shows that were updated anyway
            if curShowID in toRefresh and curShowID not in toUpdate:
                try:
                    settings.showQueueScheduler.action.refresh_show(show_obj, force=True)
                    refreshes.append(show_obj.name)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh show {show_name}: {exception_format}").format(show_name=show_obj.name, exception_format=e))

            if curShowID in toRename:
                settings.showQueueScheduler.action.rename_show_episodes(show_obj)
                renames.append(show_obj.name)

            if curShowID in toSubtitle:
                settings.showQueueScheduler.action.download_subtitles(show_obj)
                subtitles.append(show_obj.name)

        if errors:
            ui.notifications.error(_("Errors encountered"), "<br >\n".join(errors))

        messageDetail = ""

        if updates:
            messageDetail += "<br><b>" + _("Updates") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(updates)
            messageDetail += "</li></ul>"

        if refreshes:
            messageDetail += "<br><b>" + _("Refreshes") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(refreshes)
            messageDetail += "</li></ul>"

        if renames:
            messageDetail += "<br><b>" + _("Renames") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(renames)
            messageDetail += "</li></ul>"

        if subtitles:
            messageDetail += "<br><b>" + _("Subtitles") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(subtitles)
            messageDetail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            ui.notifications.message(_("The following actions were queued") + ":", messageDetail)

        return self.redirect("/manage/")

    def failedDownloads(self, limit=100, toRemove=None):
        failed_db_con = db.DBConnection("failed.db")

        if limit == "0":
            sql_results = failed_db_con.select("SELECT * FROM failed")
        else:
            sql_results = failed_db_con.select("SELECT * FROM failed LIMIT ?", [limit])

        toRemove = toRemove.split("|") if toRemove else []

        for release in toRemove:
            failed_db_con.action("DELETE FROM failed WHERE failed.release = ?", [release])

        if toRemove:
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
