import os
import traceback
from collections import namedtuple

import dateutil.parser

import sickchill
from sickchill import logger, settings
from sickchill.helper.common import sanitize_filename
from sickchill.helper.exceptions import (
    CantRefreshShowException,
    CantRemoveShowException,
    CantUpdateShowException,
    EpisodeDeletedException,
    MultipleShowObjectsException,
    ShowDirectoryNotFoundException,
)
from sickchill.oldbeard.trakt_api import TraktAPI
from sickchill.show.Show import Show
from sickchill.tv import TVShow

from . import generic_queue, name_cache, notifiers, scene_numbering, ui
from .blackandwhitelist import BlackAndWhiteList
from .common import WANTED
from .helpers import chmodAsParent, makeDir, sortable_name


class ShowQueue(generic_queue.GenericQueue):
    def __init__(self):
        super(ShowQueue, self).__init__()
        self.queue_name = "SHOWQUEUE"

    def _is_in_queue(self, show, actions):
        if not show:
            return False

        return show.indexerid in (x.show.indexerid if x.show else 0 for x in self.queue if x.action_id in actions)

    def _is_being_somethinged(self, show, actions):
        return self.currentItem is not None and show == self.currentItem.show and self.currentItem.action_id in actions

    # def is_in_add_queue(self, show):
    #     return self._isInQueue(show, (ShowQueueActions.ADD,))

    def is_in_update_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def is_in_refresh_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.REFRESH,))

    def is_in_rename_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.RENAME,))

    def is_in_remove_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.REMOVE,))

    def is_in_subtitle_queue(self, show):
        return self._is_in_queue(show, (ShowQueueActions.SUBTITLE,))

    def is_being_added(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.ADD,))

    def is_being_updated(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.UPDATE, ShowQueueActions.FORCEUPDATE))

    def is_being_refreshed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.REFRESH,))

    def is_being_renamed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.RENAME,))

    def is_being_removed(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.REMOVE,))

    def is_being_subtitled(self, show):
        return self._is_being_somethinged(show, (ShowQueueActions.SUBTITLE,))

    @property
    def loading_show_list(self):
        return {x for x in self.queue + [self.currentItem] if x and x.is_loading}

    def update_show(self, show, force=False):

        if self.is_being_added(show):
            raise CantUpdateShowException(f"{show.name} is still being added, wait until it is finished before you update.")

        if self.is_being_updated(show):
            raise CantUpdateShowException(f"{show.name} is already being updated by Post-processor or manually started, can't update again until it's done.")

        if self.is_in_update_queue(show):
            raise CantUpdateShowException(
                f"{show.name} is in process of being updated by Post-processor or manually started, can't update again until it's done."
            )

        queue_item_obj = QueueItemUpdate(show, force=force)
        self.add_item(queue_item_obj)
        return queue_item_obj

    def refresh_show(self, show, force=False):

        if self.is_being_refreshed(show) and not force:
            raise CantRefreshShowException("This show is already being refreshed, not refreshing again.")

        if self.is_being_updated(show) or self.is_in_update_queue(show):
            logger.debug(
                "A refresh was attempted but there is already an update queued or in progress. Updates do a refresh at the end so I'm skipping this request."
            )
            return

        if show.paused and not force:
            logger.debug(f"Skipping show [{show.name}] because it is paused.")
            return

        logger.debug(f"Queueing show refresh for {show.name}")

        queue_item_obj = QueueItemRefresh(show, force=force)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyUnusedLocal
    def rename_show_episodes(self, show, force=False):
        queue_item_obj = QueueItemRename(show)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyUnusedLocal
    def download_subtitles(self, show, force=False):
        queue_item_obj = QueueItemSubtitle(show)
        self.add_item(queue_item_obj)
        return queue_item_obj

    # noinspection PyPep8Naming
    def add_show(
        self,
        indexer,
        indexer_id,
        showDir,
        default_status=None,
        quality=None,
        season_folders=None,
        lang=None,
        subtitles=None,
        subtitles_sr_metadata=None,
        anime=None,
        scene=None,
        paused=None,
        blacklist=None,
        whitelist=None,
        default_status_after=None,
        root_dir=None,
    ):

        if lang is None:
            lang = settings.INDEXER_DEFAULT_LANGUAGE

        if default_status_after is None:
            default_status_after = settings.STATUS_DEFAULT_AFTER

        queue_item_obj = QueueItemAdd(
            indexer,
            indexer_id,
            showDir,
            default_status,
            quality,
            season_folders,
            lang,
            subtitles,
            subtitles_sr_metadata,
            anime,
            scene,
            paused,
            blacklist,
            whitelist,
            default_status_after,
            root_dir,
        )

        self.add_item(queue_item_obj)
        return queue_item_obj

    def remove_show(self, show, full=False):
        if not show:
            raise CantRemoveShowException("Failed removing show: Show does not exist")

        if not hasattr(show, "indexerid"):
            raise CantRemoveShowException("Failed removing show: Show does not have an indexer id")

        if self._is_in_queue(show, (ShowQueueActions.REMOVE,)):
            raise CantRemoveShowException(f"{show.name} is already queued to be removed")

        # remove other queued actions for this show.
        for item in self.queue:
            if item and item.show and item != self.currentItem and show.indexerid == item.show.indexerid:
                self.queue.remove(item)

        queue_item_obj = QueueItemRemove(show=show, full=full)
        self.add_item(queue_item_obj)
        return queue_item_obj


class ShowQueueActions(object):
    def __init__(self):
        pass

    REFRESH = 1
    ADD = 2
    UPDATE = 3
    FORCEUPDATE = 4
    RENAME = 5
    SUBTITLE = 6
    REMOVE = 7

    names = {
        REFRESH: _("Refresh"),
        ADD: _("Add"),
        UPDATE: _("Update"),
        FORCEUPDATE: _("Force Update"),
        RENAME: _("Rename"),
        SUBTITLE: _("Subtitle"),
        REMOVE: _("Remove Show"),
    }


class ShowQueueItem(generic_queue.QueueItem):
    """
    Represents an item in the queue waiting to be executed

    Can be either:
    - show being added (may or may not be associated with a show object)
    - show being refreshed
    - show being updated
    - show being force updated
    - show being subtitled
    """

    def __init__(self, action_id, show):
        super(ShowQueueItem, self).__init__(ShowQueueActions.names[action_id], action_id)
        self.show = show

    def is_in_queue(self):
        return self in settings.showQueueScheduler.action.queue + [settings.showQueueScheduler.action.currentItem]

    @property
    def show_name(self):
        return self.show.name if self.show else "UNSET"

    @property
    def is_loading(self):
        return False


class QueueItemAdd(ShowQueueItem):
    # noinspection PyPep8Naming
    def __init__(
        self,
        indexer,
        indexer_id,
        showDir,
        default_status,
        quality,
        season_folders,
        lang,
        subtitles,
        subtitles_sr_metadata,
        anime,
        scene,
        paused,
        blacklist,
        whitelist,
        default_status_after,
        root_dir,
    ):

        super(QueueItemAdd, self).__init__(ShowQueueActions.ADD, None)

        self.showDir = showDir
        self.indexer = indexer
        self.indexer_id = indexer_id
        self.default_status = default_status
        self.quality = quality
        self.season_folders = season_folders
        self.lang = lang
        self.subtitles = subtitles
        self.subtitles_sr_metadata = subtitles_sr_metadata
        self.anime = anime
        self.scene = scene
        self.paused = paused
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.default_status_after = default_status_after
        self.root_dir = root_dir

        self.show = None

        # Process add show in priority
        self.priority = generic_queue.QueuePriorities.HIGH

    @property
    def show_name(self):
        """
        Returns the show name if there is a show object created, if not returns
        the dir that the show is being added to.
        """
        return self.show.name if self.show else self.showDir.rsplit(os.sep)[-1] if self.showDir else _("Loading")

    @property
    def is_loading(self):
        """
        Returns True if we've gotten far enough to have a show object, or False
        if we still only know the folder name.
        """
        return self.show not in settings.showList or not self.show

    @property
    def info(self):
        info = namedtuple("LoadingShowInfo", "id name sort_name network network_image_url show_image_url quality")
        if self.show:
            return info(
                id=self.show.indexerid,
                name=self.show.name,
                sort_name=self.show.sort_name,
                network=self.show.network,
                network_image_url=self.show.network_image_url,
                show_image_url=self.show.show_image_url,
                quality=self.show.quality,
            )
        # noinspection PyUnresolvedReferences
        return info(
            id=0,
            name=self.show_name,
            sort_name=sortable_name(self.show_name),
            network=_("Loading"),
            network_image_url="images/network/nonetwork.png",
            show_image_url=lambda x: "images/{}.png".format(("poster", "banner")["banner" in x]),
            quality=0,
        )

    def run(self):

        super(QueueItemAdd, self).run()

        logger.info(
            _("Starting to add show {0}").format(_("by ShowDir: {0}").format(self.showDir) if self.showDir else _("by Indexer Id: {0}").format(self.indexer_id))
        )
        # make sure the Indexer IDs are valid
        try:
            s = sickchill.indexer.series_by_id(indexerid=self.indexer_id, indexer=self.indexer, language=self.lang)
            if not s:
                error_string = _("Could not find show with id:{indexer_id} on {indexer}, skipping").format(
                    indexer_id=self.indexer_id, indexer=sickchill.indexer.name(self.indexer)
                )

                logger.info(error_string)
                ui.notifications.error(_("Unable to add show"), error_string)

                self._finish_early()
                return

            # Let's try to create the show Dir if it's not provided. This way we force the show dir to build build using the
            # Indexers provided series name
            if self.root_dir and not self.showDir:
                if not s.seriesName:
                    logger.info(_("Unable to get a show {showDir}, can't add the show").format(showDir=self.showDir))
                    self._finish_early()
                    return

                show_dir = s.seriesName
                if settings.ADD_SHOWS_WITH_YEAR and s.firstAired:
                    try:
                        year = f"({dateutil.parser.parse(s.firstAired).year})"
                        if year not in show_dir:
                            show_dir = f"{s.seriesName} {year}"
                    except (TypeError, ValueError):
                        logger.info(_("Could not append the show year folder for the show: {show_dir}").format(show_dir=show_dir))

                self.showDir = os.path.join(self.root_dir, sanitize_filename(show_dir))

                if settings.ADD_SHOWS_WO_DIR:
                    logger.info(_("Skipping initial creation of {showDir} due to config.ini setting").format(showDir=self.showDir))
                else:
                    dir_exists = makeDir(self.showDir)
                    if not dir_exists:
                        logger.info(_("Unable to create the folder {showDir}, can't add the show").format(showDir=self.showDir))
                        self._finish_early()
                        return

                    chmodAsParent(self.showDir)

            # this usually only happens if they have an NFO in their show dir which gave us a Indexer ID that has no proper english version of the show
            if getattr(s, "seriesName", None) is None:
                # noinspection PyPep8
                error_string = _(
                    "Show in {showDir} has no name on {indexer}, probably "
                    "searched with the wrong language. Delete .nfo and add manually in the correct language."
                ).format(showDir=self.showDir, indexer=sickchill.indexer.name(self.indexer))

                logger.warning(error_string)
                ui.notifications.error(_("Unable to add show"), error_string)

                self._finish_early()
                return
        except Exception as error:
            error_string = (
                f"Unable to look up the show in {self.showDir} on {sickchill.indexer.name(self.indexer)} "
                f"using ID {self.indexer_id}, not using the NFO. Delete .nfo and try adding manually again."
            )

            logger.exception(f"{error_string}: {error}")
            ui.notifications.error(_("Unable to add show"), error_string)

            if settings.USE_TRAKT:
                trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)

                title = self.showDir.split("/")[-1]
                data = {"shows": [{"title": title, "ids": {sickchill.indexer.slug(self.indexer): self.indexer_id}}]}
                trakt_api.traktRequest("sync/watchlist/remove", data, method="POST")

            self._finish_early()
            return

        try:
            try:
                newShow = TVShow(self.indexer, self.indexer_id, self.lang)
            except MultipleShowObjectsException as error:
                # If we have the show in our list, but the location is wrong, lets fix it and refresh!
                existing_show = Show.find(settings.showList, self.indexer_id)
                # noinspection PyProtectedMember
                if existing_show and not os.path.isdir(existing_show._location):
                    newShow = existing_show
                else:
                    raise error

            newShow.loadFromIndexer()

            self.show = newShow

            # set up initial values
            self.show.location = self.showDir
            self.show.subtitles = self.subtitles if self.subtitles is not None else settings.SUBTITLES_DEFAULT
            self.show.subtitles_sr_metadata = self.subtitles_sr_metadata
            self.show.quality = self.quality if self.quality else settings.QUALITY_DEFAULT
            self.show.season_folders = self.season_folders if self.season_folders is not None else settings.SEASON_FOLDERS_DEFAULT
            self.show.anime = self.anime if self.anime is not None else settings.ANIME_DEFAULT
            self.show.scene = self.scene if self.scene is not None else settings.SCENE_DEFAULT
            self.show.paused = self.paused if self.paused is not None else False

            # set up default new/missing episode status
            logger.info(_("Setting all episodes to the specified default status: {default_status}").format(default_status=self.default_status))
            self.show.default_ep_status = self.default_status

            if self.show.anime:
                self.show.release_groups = BlackAndWhiteList(self.show.indexerid)
                if self.blacklist:
                    self.show.release_groups.set_black_keywords(self.blacklist)
                if self.whitelist:
                    self.show.release_groups.set_white_keywords(self.whitelist)

            # # be smart-ish about this
            # if self.show.genre and 'talk show' in self.show.genre.lower():
            #     self.show.air_by_date = 1
            # if self.show.genre and 'documentary' in self.show.genre.lower():
            #     self.show.air_by_date = 0
            # if self.show.classification and 'sports' in self.show.classification.lower():
            #     self.show.sports = 1

        except Exception as error:
            error_string = f"Unable to add {self.show.name if self.show else 'show'} due to an error with {sickchill.indexer.name(self.indexer)}"

            logger.exception(f"{error_string}: {error}")

            logger.exception(f"Error trying to add show: {error}")
            logger.debug(traceback.format_exc())

            ui.notifications.error(_("Unable to add show"), error_string)

            self._finish_early()
            return

        except MultipleShowObjectsException:
            error_string = _("The show in {showDir} is already in your show list, skipping").format(showDir=self.showDir)
            logger.warning(error_string)
            ui.notifications.error(_("Show skipped"), error_string)

            self._finish_early()
            return

        self.show.load_imdb_info()

        try:
            self.show.saveToDB()
        except Exception as error:
            logger.exception(f"Error saving the show to the database: {error}")
            logger.debug(traceback.format_exc())
            self._finish_early()
            raise

        # add it to the show list
        if not Show.find(settings.showList, self.indexer_id):
            settings.showList.append(self.show)

        try:
            self.show.loadEpisodesFromIndexer()
        except Exception as error:
            logger.exception(f"Error with {self.show.idxr.name}, not creating episode list: {error}")
            logger.debug(traceback.format_exc())

        # update internal name cache
        name_cache.build_name_cache(self.show)

        try:
            self.show.loadEpisodesFromDir()
        except Exception as error:
            logger.exception(f"Error searching dir for episodes: {error}")
            logger.debug(traceback.format_exc())

        # if they set default ep status to WANTED then run the backlog to search for episodes
        # FIXME: This needs to be a backlog queue item!!!
        if self.show.default_ep_status == WANTED:
            logger.info("Launching backlog for this show since its episodes are WANTED")
            settings.backlogSearchScheduler.action.searchBacklog([self.show])

        self.show.writeMetadata()
        self.show.updateMetadata()
        self.show.populateCache()

        self.show.flushEpisodes()

        if settings.USE_TRAKT:
            # if there are specific episodes that need to be added by trakt
            settings.traktCheckerScheduler.action.manageNewShow(self.show)
            # add show to trakt.tv library
            if settings.TRAKT_SYNC:
                settings.traktCheckerScheduler.action.addShowToTraktLibrary(self.show)

            if settings.TRAKT_SYNC_WATCHLIST:
                logger.info("update watchlist")
                notifiers.trakt_notifier.update_watchlist(show_obj=self.show)

        # Load XEM data to DB for show
        scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer, force=True)

        # check if show has XEM mapping so we can determine if searches should go by scene numbering or indexer numbering.
        if not self.scene and scene_numbering.get_xem_numbering_for_show(self.show.indexerid, self.show.indexer):
            self.show.scene = 1

        # After initial add, set to default_status_after.
        self.show.default_ep_status = self.default_status_after

        super(QueueItemAdd, self).finish()
        self.finish()

    def _finish_early(self):
        if self.show is not None:
            settings.showQueueScheduler.action.remove_show(self.show)

        super(QueueItemAdd, self).finish()
        self.finish()


class QueueItemRefresh(ShowQueueItem):
    def __init__(self, show=None, force=False):
        super(QueueItemRefresh, self).__init__(ShowQueueActions.REFRESH, show)

        # do refreshes first because they're quick
        self.priority = generic_queue.QueuePriorities.HIGH

        # force refresh certain items
        self.force = force

    def run(self):

        super(QueueItemRefresh, self).run()

        logger.info(f"Performing refresh on {self.show.name}")

        self.show.refreshDir()
        self.show.writeMetadata()
        if self.force:
            self.show.updateMetadata()
        self.show.populateCache()

        # Load XEM data to DB for show
        scene_numbering.xem_refresh(self.show.indexerid, self.show.indexer)

        super(QueueItemRefresh, self).finish()
        self.finish()


class QueueItemRename(ShowQueueItem):
    def __init__(self, show=None):
        super(QueueItemRename, self).__init__(ShowQueueActions.RENAME, show)

    def run(self):

        super(QueueItemRename, self).run()

        logger.info(f"Performing rename on {self.show.name}")

        try:
            self.show.location
        except ShowDirectoryNotFoundException:
            logger.warning(f"Can't perform rename on {self.show.name} when the show dir is missing.")
            super(QueueItemRename, self).finish()
            self.finish()
            return

        ep_obj_rename_list = []

        ep_obj_list = self.show.getAllEpisodes(has_location=True)
        for cur_ep_obj in ep_obj_list:
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                # do we have one of multi-episodes in the rename list already
                for cur_related_ep in cur_ep_obj.relatedEps + [cur_ep_obj]:
                    if cur_related_ep in ep_obj_rename_list:
                        break
                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        for cur_ep_obj in ep_obj_rename_list:
            cur_ep_obj.rename()

        super(QueueItemRename, self).finish()
        self.finish()


class QueueItemSubtitle(ShowQueueItem):
    def __init__(self, show=None):
        super(QueueItemSubtitle, self).__init__(ShowQueueActions.SUBTITLE, show)

    def run(self):
        super(QueueItemSubtitle, self).run()

        logger.info(f"Downloading subtitles for {self.show.name} ")

        self.show.download_subtitles()

        super(QueueItemSubtitle, self).finish()
        self.finish()


class QueueItemUpdate(ShowQueueItem):
    def __init__(self, show=None, force=False):
        action = ShowQueueActions.FORCEUPDATE if force else ShowQueueActions.UPDATE
        super(QueueItemUpdate, self).__init__(action, show)
        self.force = force
        self.priority = generic_queue.QueuePriorities.HIGH

    def run(self):

        super(QueueItemUpdate, self).run()

        logger.debug(f"Beginning update of {self.show.name}")

        logger.debug(f"Retrieving show info from {self.show.idxr.name}")
        try:
            self.show.loadFromIndexer()
        except Exception as error:
            logger.warning(f"Unable to contact {self.show.idxr.name}, aborting: {error}")
            super(QueueItemUpdate, self).finish()
            self.finish()
            return

        self.show.load_imdb_info()

        # have to save show before reading episodes from db
        try:
            self.show.saveToDB()
        except Exception as error:
            logger.exception(f"Error saving show info to the database: {error}")
            logger.debug(traceback.format_exc())

        # get episode list from DB
        DBEpList = self.show.loadEpisodesFromDB()

        # get episode list from TVDB
        logger.debug(f"Loading all episodes from {self.show.idxr.name}")
        try:
            IndexerEpList = self.show.loadEpisodesFromIndexer()
        except Exception as error:
            logger.exception(f"Unable to get info from {self.show.idxr.name}, the show info will not be refreshed: {error}")
            IndexerEpList = None

        if IndexerEpList:
            for curSeason in IndexerEpList:
                for curEpisode in IndexerEpList[curSeason]:
                    curEp = self.show.getEpisode(curSeason, curEpisode)
                    curEp.saveToDB()

                    if curSeason in DBEpList and curEpisode in DBEpList[curSeason]:
                        del DBEpList[curSeason][curEpisode]

            # remaining episodes in the DB list are not on the indexer, just delete them from the DB
            for curSeason in DBEpList:
                for curEpisode in DBEpList[curSeason]:
                    logger.info("Permanently deleting episode {0:02d}E{1:02d} from the database".format(curSeason, curEpisode))
                    curEp = self.show.getEpisode(curSeason, curEpisode)
                    try:
                        curEp.deleteEpisode()
                    except EpisodeDeletedException:
                        pass

        #  save show again, in case episodes have changed
        try:
            self.show.saveToDB()
        except Exception as error:
            logger.exception(f"Error saving show info to the database: {error}")
            logger.debug(traceback.format_exc())

        logger.debug(f"Finished update of {self.show.name}")

        # oldbeard.showQueueScheduler.action.refresh_show(self.show, self.force)
        QueueItemRefresh(self.show, self.force).run()
        super(QueueItemUpdate, self).finish()
        self.finish()


class QueueItemRemove(ShowQueueItem):
    def __init__(self, show=None, full=False):
        super(QueueItemRemove, self).__init__(ShowQueueActions.REMOVE, show)

        # lets make sure this happens before any other high priority actions
        self.priority = generic_queue.QueuePriorities.HIGH**2
        self.full = full

    def run(self):
        super(QueueItemRemove, self).run()
        logger.info(f"Removing {self.show.name}")
        self.show.deleteShow(full=self.full)

        if settings.USE_TRAKT:
            try:
                settings.traktCheckerScheduler.action.removeShowFromTraktLibrary(self.show)
            except Exception as error:
                logger.warning(_("Unable to delete show from Trakt: {show_name}. Error: {error}").format(show_name=self.show.name, error=error))

        # If any notification fails, don't stop removal
        try:
            # TODO: ep_obj is undefined here, so all of these will fail.
            # send notifications
            # notifiers.notify_download(ep_obj._format_pattern('%SN - %Sx%0E - %EN - %QN'))

            # do the library update for KODI
            notifiers.kodi_notifier.update_library(self.show.name)

            # do the library update for Plex
            notifiers.plex_notifier.update_library(self.show)

            # do the library update for EMBY
            notifiers.emby_notifier.update_library(self.show)

            # do the library update for NMJ
            # nmj_notifier kicks off its library update when the notify_download is issued (inside notifiers)

            # do the library update for Synology Indexer
            notifiers.synoindex_notifier.addFolder(self.show._location)

            # do the library update for pyTivo
            notifiers.pytivo_notifier.update_library(self.show)
        except Exception:
            logger.info(_("Some notifications could not be sent. Continuing removal of {}...").format(self.show.name))

        super(QueueItemRemove, self).finish()
        self.finish()
