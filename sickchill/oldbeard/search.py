import datetime
import os
import re
import threading
import traceback

import sickchill.oldbeard.name_cache
import sickchill.oldbeard.providers
from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.helper.exceptions import AuthException
from sickchill.providers.GenericProvider import GenericProvider

from . import clients, common, db, failed_history, helpers, history, notifiers, nzbget, nzbSplitter, sab, show_name_helpers, ui
from .common import MULTI_EP_RESULT, Quality, SEASON_RESULT, SNATCHED, SNATCHED_BEST, SNATCHED_PROPER
from .name_parser.parser import InvalidNameException, InvalidShowException, NameParser


def _downloadResult(result):
    """
    Downloads a result to the appropriate black hole folder.

    :param result: SearchResult instance to download.
    :return: boolean, True on success
    """

    resProvider = result.provider
    if resProvider is None:
        logger.exception("Invalid provider name - this is a coding error, report it please")
        return False

    # nzbs/torrents with an URL can just be downloaded from the provider
    if result.resultType in (GenericProvider.NZB, GenericProvider.TORRENT):
        newResult = resProvider.download_result(result)
    # if it's an nzb data result
    elif result.resultType == GenericProvider.NZBDATA:

        # get the final file path to the nzb
        file_name = os.path.join(settings.NZB_DIR, result.name + ".nzb")

        logger.info("Saving NZB to " + file_name)

        newResult = True

        # save the data to disk
        try:
            with open(file_name, 'w') as fileOut:
                fileOut.write(result.extraInfo[0])

            helpers.chmodAsParent(file_name)

        except EnvironmentError as e:
            logger.exception("Error trying to save NZB to black hole: " + str(e))
            newResult = False
    else:
        logger.exception("Invalid provider type - this is a coding error, report it please")
        newResult = False

    return newResult


def snatchEpisode(result, endStatus=SNATCHED):
    """
    Contains the internal logic necessary to actually "snatch" a result that
    has been found.

    :param result: SearchResult instance to be snatched.
    :param endStatus: the episode status that should be used for the episode object once it's snatched.
    :return: boolean, True on success
    """

    if result is None:
        return False

    result.priority = 0  # -1 = low, 0 = normal, 1 = high
    if settings.ALLOW_HIGH_PRIORITY:
        # if it aired recently make it high priority
        for curEp in result.episodes:
            if datetime.date.today() - curEp.airdate <= datetime.timedelta(days=7):
                result.priority = 1

    endStatus = SNATCHED_PROPER if re.search(r'\b(proper|repack|real)\b', result.name, re.I) else endStatus

    # This is breaking if newznab protocol, expecting a torrent from a url and getting a magnet instead.
    if result.url and 'jackett_apikey' in result.url:
        response = result.provider.get_url(result.url, allow_redirects=False, returns='response')
        if response.next and response.next.url and response.next.url.startswith('magnet'):
            result.url = response.next.url

    # NZBs can be sent straight to SAB or saved to disk
    if result.resultType in (GenericProvider.NZB, GenericProvider.NZBDATA):
        if settings.NZB_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        elif settings.NZB_METHOD == "sabnzbd":
            dlResult = sab.sendNZB(result)
        elif settings.NZB_METHOD == "nzbget":
            is_proper = True if endStatus == SNATCHED_PROPER else False
            dlResult = nzbget.sendNZB(result, is_proper)
        elif settings.NZB_METHOD == "download_station":
            client = clients.getClientInstance(settings.NZB_METHOD)(
                settings.SYNOLOGY_DSM_HOST, settings.SYNOLOGY_DSM_USERNAME, settings.SYNOLOGY_DSM_PASSWORD)
            dlResult = client.sendNZB(result)
        else:
            logger.exception("Unknown NZB action specified in config: " + settings.NZB_METHOD)
            dlResult = False

    # Torrents can be sent to clients or saved to disk
    elif result.resultType == GenericProvider.TORRENT:
        # torrents are saved to disk when blackhole mode
        if settings.TORRENT_METHOD == "blackhole":
            dlResult = _downloadResult(result)
        else:
            if not result.content and not result.url.startswith('magnet'):
                if result.provider.login():
                    result.content = result.provider.get_url(result.url, returns='content')

            if result.content or result.url.startswith('magnet'):
                client = clients.getClientInstance(settings.TORRENT_METHOD)()
                dlResult = client.sendTORRENT(result)
            else:
                logger.warning("Torrent file content is empty")
                dlResult = False
    else:
        logger.exception("Unknown result type, unable to download it ({0!r})".format(result.resultType))
        dlResult = False

    if not dlResult:
        return False

    if settings.USE_FAILED_DOWNLOADS:
        failed_history.logSnatch(result)

    ui.notifications.message('Episode snatched', result.name)

    history.logSnatch(result)

    # don't notify when we re-download an episode
    sql_l = []
    trakt_data = []
    for curEpObj in result.episodes:
        with curEpObj.lock:
            if isFirstBestMatch(result):
                curEpObj.status = Quality.compositeStatus(SNATCHED_BEST, result.quality)
            else:
                curEpObj.status = Quality.compositeStatus(endStatus, result.quality)

            sql_l.append(curEpObj.get_sql())

        if curEpObj.status not in Quality.DOWNLOADED:
            try:
                notifiers.notify_snatch("{0} from {1}".format(curEpObj._format_pattern('%SN - %Sx%0E - %EN - %QN'), result.provider.name))
            except Exception:
                # Without this, when notification fail, it crashes the snatch thread and SR will
                # keep snatching until notification is sent
                logger.debug("Failed to send snatch notification")

            trakt_data.append((curEpObj.season, curEpObj.episode))

    data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)

    if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
        logger.debug("Add episodes, showid: indexerid " + str(result.show.indexerid) + ", Title " + str(result.show.name) + " to Traktv Watchlist")
        if data:
            notifiers.trakt_notifier.update_watchlist(result.show, data_episode=data, update="add")

    if sql_l:
        main_db_con = db.DBConnection()
        main_db_con.mass_action(sql_l)

    return True


def pickBestResult(results, show):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param show: Shows we check for
    :return: best result object
    """
    results = results if isinstance(results, list) else [results]

    logger.debug("Picking the best result out of " + str([x.name for x in results]))

    bestResult = None

    # order the list so that preferred releases are at the top
    results.sort(key=lambda ep: show_name_helpers.hasPreferredWords(ep.name, ep.show), reverse=True)

    # find the best result for the current episode
    for cur_result in results:
        if show and cur_result.show is not show:
            continue

        # build the black And white list
        if show.is_anime:
            if not show.release_groups.is_valid(cur_result):
                continue

        logger.info("Quality of " + cur_result.name + " is " + Quality.qualityStrings[cur_result.quality])

        anyQualities, bestQualities = Quality.splitQuality(show.quality)

        if cur_result.quality not in anyQualities + bestQualities:
            logger.debug(cur_result.name + " is a quality we know we don't want, rejecting it")
            continue

        if not show_name_helpers.filter_bad_releases(cur_result.name, parse=False, show=show):
            continue

        if hasattr(cur_result, 'size'):
            if settings.USE_FAILED_DOWNLOADS and failed_history.hasFailed(cur_result.name, cur_result.size,
                                                                          cur_result.provider.name):
                logger.info(cur_result.name + " has previously failed, rejecting it")
                continue

        if not bestResult:
            bestResult = cur_result
        elif cur_result.quality in bestQualities and (bestResult.quality < cur_result.quality or bestResult.quality not in bestQualities):
            bestResult = cur_result
        elif cur_result.quality in anyQualities and bestResult.quality not in bestQualities and bestResult.quality < cur_result.quality:
            bestResult = cur_result
        elif bestResult.quality == cur_result.quality:
            if "proper" in cur_result.name.lower() or "real" in cur_result.name.lower() or "repack" in cur_result.name.lower():
                logger.info("Preferring " + cur_result.name + " (repack/proper/real over nuked)")
                bestResult = cur_result
            elif "internal" in bestResult.name.lower() and "internal" not in cur_result.name.lower():
                logger.info("Preferring " + cur_result.name + " (normal instead of internal)")
                bestResult = cur_result
            elif "xvid" in bestResult.name.lower() and "x264" in cur_result.name.lower():
                logger.info("Preferring " + cur_result.name + " (x264 over xvid)")
                bestResult = cur_result

    if bestResult:
        logger.debug("Picked " + bestResult.name + " as the best")
    else:
        logger.debug("No result picked.")

    return bestResult


def isFinalResult(result):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    :param result: quality to check
    :return: True if the result is the highest quality in both the any/best quality lists else False
    """

    logger.debug("Checking if we should keep searching after we've found " + result.name)

    show_obj = result.episodes[0].show

    any_qualities, best_qualities = Quality.splitQuality(show_obj.quality)

    # if there is a re-download that's higher than this then we definitely need to keep looking
    if best_qualities and result.quality < max(best_qualities):
        return False

    # if it does not match the shows black and white list its no good
    elif show_obj.is_anime and show_obj.release_groups.is_valid(result):
        return False

    # if there's no re-download that's higher (above) and this is the highest initial download then we're good
    elif any_qualities and result.quality in any_qualities:
        return True

    elif best_qualities and result.quality == max(best_qualities):
        return True

    # if we got here than it's either not on the lists, they're empty, or it's lower than the highest required
    else:
        return False


def isFirstBestMatch(result):
    """
    Checks if the given result is a best quality match and if we want to stop searching providers here.

    :param result: to check
    :return: True if the result is the best quality match else False
    """

    logger.debug("Checking if we should stop searching for a better quality for for episode " + result.name)

    show_obj = result.episodes[0].show

    any_qualities_, best_qualities = Quality.splitQuality(show_obj.quality)

    return result.quality in best_qualities if best_qualities else False


def wantedEpisodes(show, fromDate):
    """
    Get a list of episodes that we want to download
    :param show: Show these episodes are from
    :param fromDate: Search from a certain date
    :return: list of wanted episodes
    """
    wanted = []
    if show.paused:
        logger.debug("Not checking for episodes of {0} because the show is paused".format(show.name))
        return wanted

    allowed_qualities, preferred_qualities = common.Quality.splitQuality(show.quality)
    all_qualities = list(set(allowed_qualities + preferred_qualities))

    logger.debug("Seeing if we need anything from " + show.name)
    con = db.DBConnection()

    sql_results = con.select(
        "SELECT status, season, episode FROM tv_episodes WHERE showid = ? AND season > 0 and airdate > ?",
        [show.indexerid, fromDate.toordinal()]
    )

    # check through the list of statuses to see if we want any
    for result in sql_results:
        cur_status, cur_quality = common.Quality.splitCompositeStatus(int(result["status"] or -1))
        if cur_status not in {common.WANTED, common.DOWNLOADED, common.SNATCHED, common.SNATCHED_PROPER}:
            continue

        if cur_status != common.WANTED:
            if preferred_qualities:
                if cur_quality in preferred_qualities:
                    continue
            elif cur_quality in allowed_qualities:
                continue

        epObj = show.getEpisode(result["season"], result["episode"])
        epObj.wantedQuality = [i for i in all_qualities if i > cur_quality and i != common.Quality.UNKNOWN]
        wanted.append(epObj)

    return wanted


def searchForNeededEpisodes():
    """
    Check providers for details on wanted episodes

    :return: episodes we have a search hit for
    """
    foundResults = {}

    didSearch = False

    show_list = settings.showList
    fromDate = datetime.date.min
    episodes = []

    for curShow in show_list:
        if not curShow.paused:
            sickchill.oldbeard.name_cache.buildNameCache(curShow)
            episodes.extend(wantedEpisodes(curShow, fromDate))

    if not episodes:
        # nothing wanted so early out, ie: avoid whatever abritrarily
        # complex thing a provider cache update entails, for example,
        # reading rss feeds
        logger.info("No episodes needed.")
        return list(foundResults.values())

    origThreadName = threading.currentThread().name

    providers = [x for x in sickchill.oldbeard.providers.sortedProviderList(settings.RANDOMIZE_PROVIDERS) if x.is_active and x.enable_daily and x.can_daily]
    for curProvider in providers:
        threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"
        curProvider.cache.update_cache()

    for curProvider in providers:
        threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"
        try:
            curFoundResults = curProvider.search_rss(episodes)
        except AuthException as e:
            logger.warning("Authentication error: " + str(e))
            continue
        except Exception as e:
            logger.exception("Error while searching " + curProvider.name + ", skipping: " + str(e))
            logger.debug(traceback.format_exc())
            continue

        didSearch = True

        # pick a single result for each episode, respecting existing results
        for curEp in curFoundResults:
            if not curEp.show or curEp.show.paused:
                logger.debug("Skipping {0} because the show is paused ".format(curEp.pretty_name()))
                continue

            bestResult = pickBestResult(curFoundResults[curEp], curEp.show)

            # if all results were rejected move on to the next episode
            if not bestResult:
                logger.debug("All found results for " + curEp.pretty_name() + " were rejected.")
                continue

            # if it's already in the list (from another provider) and the newly found quality is no better then skip it
            if curEp in foundResults and bestResult.quality <= foundResults[curEp].quality:
                continue

            foundResults[curEp] = bestResult

    threading.currentThread().name = origThreadName

    if not didSearch:
        logger.info("No NZB/Torrent providers found or enabled in the sickchill config for daily searches. Please check your settings.")

    return list(foundResults.values())


def searchProviders(show, episodes, manualSearch=False, downCurQuality=False):
    """
    Walk providers for information on shows

    :param show: Show we are looking for
    :param episodes: Episodes we hope to find
    :param manualSearch: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we re-download currently available quality file
    :return: results for search
    """
    foundResults = {}
    finalResults = []

    didSearch = False

    # build name cache for show
    sickchill.oldbeard.name_cache.buildNameCache(show)

    origThreadName = threading.currentThread().name

    providers = [x for x in sickchill.oldbeard.providers.sortedProviderList(settings.RANDOMIZE_PROVIDERS) if x.is_active and x.can_backlog and x.enable_backlog]
    for curProvider in providers:
        threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"
        curProvider.cache.update_cache()

    threading.currentThread().name = origThreadName

    for curProvider in providers:
        threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"

        if curProvider.anime_only and not show.is_anime:
            logger.debug("" + str(show.name) + " is not an anime, skipping")
            continue

        foundResults[curProvider.name] = {}

        searchCount = 0
        search_mode = curProvider.search_mode

        # Always search for episode when manually searching when in sponly
        if search_mode == 'sponly' and manualSearch is True:
            search_mode = 'eponly'

        while True:
            searchCount += 1

            logger.info(_("Performing {episode_or_season} search for {show}").format(
                episode_or_season=(_('season pack'), _('episode'))[search_mode == 'eponly'], show=show.name))

            try:
                searchResults = curProvider.find_search_results(show, episodes, search_mode, manualSearch, downCurQuality)
            except AuthException as error:
                logger.warning("Authentication error: {0!r}".format(error))
                break
            except Exception as error:
                logger.exception("Exception while searching {0}. Error: {1!r}".format(curProvider.name, error))
                logger.debug(traceback.format_exc())
                break

            didSearch = True

            if len(searchResults):
                # make a list of all the results for this provider
                for curEp in searchResults:
                    if curEp in foundResults[curProvider.name]:
                        foundResults[curProvider.name][curEp] += searchResults[curEp]
                    else:
                        foundResults[curProvider.name][curEp] = searchResults[curEp]

                break
            elif not curProvider.search_fallback or searchCount == 2:
                break

            if search_mode == 'sponly':
                logger.debug("Fallback episode search initiated")
                search_mode = 'eponly'
            else:
                logger.debug("Fallback season pack search initiate")
                search_mode = 'sponly'

        # skip to next provider if we have no results to process
        if not foundResults[curProvider.name]:
            continue

        # pick the best season NZB
        bestSeasonResult = None
        if SEASON_RESULT in foundResults[curProvider.name]:
            bestSeasonResult = pickBestResult(foundResults[curProvider.name][SEASON_RESULT], show)

        highest_quality_overall = 0
        for cur_episode in foundResults[curProvider.name]:
            for cur_result in foundResults[curProvider.name][cur_episode]:
                if cur_result.quality != Quality.UNKNOWN and cur_result.quality > highest_quality_overall:
                    highest_quality_overall = cur_result.quality
        logger.debug("The highest quality of any match is " + Quality.qualityStrings[highest_quality_overall])

        # see if every episode is wanted
        if bestSeasonResult:
            searchedSeasons = {str(x.season) for x in episodes}

            # get the quality of the season nzb
            seasonQual = bestSeasonResult.quality
            logger.info("The quality of the season " + bestSeasonResult.provider.provider_type + " is " + Quality.qualityStrings[seasonQual])

            main_db_con = db.DBConnection()
            allEps = [int(x["episode"])
                      for x in main_db_con.select("SELECT episode FROM tv_episodes WHERE showid = ? AND ( season IN ( " + ','.join(searchedSeasons) + " ) )",
                                                  [show.indexerid])]

            logger.info(
                "Executed query: [SELECT episode FROM tv_episodes WHERE showid = {0} AND season in  {1}]".format(show.indexerid, ','.join(searchedSeasons)))
            logger.debug("Episode list: " + str(allEps))

            allWanted = True
            anyWanted = False
            for curEpNum in allEps:
                for season in {x.season for x in episodes}:
                    if not show.wantEpisode(season, curEpNum, seasonQual, downCurQuality):
                        allWanted = False
                    else:
                        anyWanted = True

            # if we need every ep in the season and there's nothing better then just download this and be done with it (unless single episodes are preferred)
            if allWanted and bestSeasonResult.quality == highest_quality_overall:
                logger.info(
                    "Every ep in this season is needed, downloading the whole " + bestSeasonResult.provider.provider_type + " " + bestSeasonResult.name)
                epObjs = []
                for curEpNum in allEps:
                    for season in {x.season for x in episodes}:
                        epObjs.append(show.getEpisode(season, curEpNum))
                bestSeasonResult.episodes = epObjs

                # Remove provider from thread name before return results
                threading.currentThread().name = origThreadName

                return [bestSeasonResult]

            elif not anyWanted:
                logger.info("No eps from this season are wanted at this quality, ignoring the result of " + bestSeasonResult.name)

            else:

                if bestSeasonResult.resultType != GenericProvider.TORRENT:
                    logger.debug("Breaking apart the NZB and adding the individual ones to our results")

                    # if not, break it apart and add them as the lowest priority results
                    individualResults = nzbSplitter.split_result(bestSeasonResult)
                    for curResult in individualResults:
                        if len(curResult.episodes) == 1:
                            epNum = curResult.episodes[0].episode
                        elif len(curResult.episodes) > 1:
                            epNum = MULTI_EP_RESULT

                        if epNum in foundResults[curProvider.name]:
                            foundResults[curProvider.name][epNum].append(curResult)
                        else:
                            foundResults[curProvider.name][epNum] = [curResult]

                # If this is a torrent all we can do is leech the entire torrent, user will have to select which eps not do download in his torrent client
                else:

                    # Season result from Torrent Provider must be a full-season torrent, creating multi-ep result for it.
                    logger.info(
                        "Adding multi-ep result for full-season torrent. Set the episodes you don't want to 'don't download' in your torrent client if desired!")
                    epObjs = []
                    for curEpNum in allEps:
                        for season in {x.season for x in episodes}:
                            epObjs.append(show.getEpisode(season, curEpNum))
                    bestSeasonResult.episodes = epObjs

                    if MULTI_EP_RESULT in foundResults[curProvider.name]:
                        foundResults[curProvider.name][MULTI_EP_RESULT].append(bestSeasonResult)
                    else:
                        foundResults[curProvider.name][MULTI_EP_RESULT] = [bestSeasonResult]

        # go through multi-ep results and see if we really want them or not, get rid of the rest
        multiResults = {}
        if MULTI_EP_RESULT in foundResults[curProvider.name]:
            for _multiResult in foundResults[curProvider.name][MULTI_EP_RESULT]:

                logger.debug("Seeing if we want to bother with multi-episode result " + _multiResult.name)

                # Filter result by ignore/required/whitelist/blacklist/quality, etc
                multiResult = pickBestResult(_multiResult, show)
                if not multiResult:
                    continue

                # see how many of the eps that this result covers aren't covered by single results
                neededEps = []
                notNeededEps = []
                for epObj in multiResult.episodes:
                    # if we have results for the episode
                    if epObj.episode in foundResults[curProvider.name] and len(foundResults[curProvider.name][epObj.episode]) > 0:
                        notNeededEps.append(epObj.episode)
                    else:
                        neededEps.append(epObj.episode)

                logger.debug("Single-ep check result is neededEps: " + str(neededEps) + ", notNeededEps: " + str(notNeededEps))

                if not neededEps:
                    logger.debug("All of these episodes were covered by single episode results, ignoring this multi-episode result")
                    continue

                # check if these eps are already covered by another multi-result
                multiNeededEps = []
                multiNotNeededEps = []
                for epObj in multiResult.episodes:
                    if epObj.episode in multiResults:
                        multiNotNeededEps.append(epObj.episode)
                    else:
                        multiNeededEps.append(epObj.episode)

                logger.debug(
                    "Multi-ep check result is multiNeededEps: " + str(multiNeededEps) + ", multiNotNeededEps: " + str(
                        multiNotNeededEps))

                if not multiNeededEps:
                    logger.debug(
                        "All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                    continue

                # don't bother with the single result if we're going to get it with a multi result
                for epObj in multiResult.episodes:
                    multiResults[epObj.episode] = multiResult
                    if epObj.episode in foundResults[curProvider.name]:
                        logger.debug(
                            "A needed multi-episode result overlaps with a single-episode result for ep #" + str(
                                epObj.episode) + ", removing the single-episode results from the list")
                        del foundResults[curProvider.name][epObj.episode]

        # of all the single ep results narrow it down to the best one for each episode
        finalResults += set(multiResults.values())
        for curEp in foundResults[curProvider.name]:
            if curEp in (MULTI_EP_RESULT, SEASON_RESULT):
                continue

            if not foundResults[curProvider.name][curEp]:
                continue

            # if all results were rejected move on to the next episode
            bestResult = pickBestResult(foundResults[curProvider.name][curEp], show)
            if not bestResult:
                continue

            # add result if its not a duplicate and
            found = False
            for i, result in enumerate(finalResults):
                for bestResultEp in bestResult.episodes:
                    if bestResultEp in result.episodes:
                        if result.quality < bestResult.quality:
                            finalResults.pop(i)
                        else:
                            found = True
            if not found:
                finalResults += [bestResult]

        # check that we got all the episodes we wanted first before doing a match and snatch
        wantedEpCount = 0
        for wantedEp in episodes:
            for result in finalResults:
                if wantedEp in result.episodes and isFinalResult(result):
                    wantedEpCount += 1

        # make sure we search every provider for results unless we found everything we wanted
        if wantedEpCount == len(episodes):
            break

    if not didSearch:
        logger.info("No NZB/Torrent providers found or enabled in the sickchill config for backlog searches. Please check your settings.")

    # Remove provider from thread name before return results
    threading.currentThread().name = origThreadName
    return finalResults


def searchProvidersList(show, episodes, search_mode='eponly'):
    """
    Walk providers for information on shows

    :param show: Show we are looking for
    :param episodes: Episodes we hope to find
    :param search_mode: String, eponly|sponly: Episode search or Season Pack Search?
    :return: results for search
    """
    foundResults = {"results": []}

    didSearch = False

    origThreadName = threading.currentThread().name

    # build name cache for show
    sickchill.oldbeard.name_cache.buildNameCache(show)

    providers = [x for x in sickchill.oldbeard.providers.sortedProviderList(settings.RANDOMIZE_PROVIDERS) if x.is_active and x.can_backlog and x.enable_backlog]
    if not providers:
        logger.info("No NZB/Torrent providers found or enabled in the sickchill config for backlog searches. Please check your settings.")
        return foundResults

    episodes = [episodes]
    search_episodes = {}
    for ep in episodes:
        if ep.season not in search_episodes:
            search_episodes[ep.season] = [ep]
        elif search_mode != 'sponly':
            search_episodes[ep.season] += [ep]

    for curProvider in providers:
        threading.currentThread().name = origThreadName + " :: [" + curProvider.name + "]"

        if curProvider.anime_only and not show.is_anime:
            logger.debug("" + str(show.name) + " is not an anime, skipping")
            continue

        if curProvider.search_mode != search_mode and not curProvider.search_fallback:
            logger.debug('Skipping provider because search type does not match and fallback is disabled')
            continue

        logger.info(_("Performing {episode_or_season} search for {show}").format(
            episode_or_season=(_('season pack'), _('episode'))[search_mode == 'eponly'], show=show.name))

        curProvider.cache.update_cache()
        for ep_list in search_episodes.values():
            for episode in ep_list:
                try:
                    curProvider.show = episode.show
                    if search_mode == 'sponly':
                        search_params = curProvider.get_season_search_strings(episode)
                    else:
                        search_params = curProvider.get_episode_search_strings(episode)

                    searchResults = curProvider.search(search_params[0], ep_obj=episode)
                except AuthException as error:
                    logger.warning("Authentication error: {0!r}".format(error))
                    continue
                except Exception as error:
                    logger.exception("Exception while searching {0}. Error: {1!r}".format(curProvider.name, error))
                    logger.debug(traceback.format_exc())
                    continue

                didSearch = True

                # make a list of all the results for this provider
                for curResult in searchResults:
                    curResult["show"] = episode.show.indexerid
                    curResult["season"] = episode.season
                    curResult["episode"] = episode.episode
                    curResult["provider"] = curProvider.name
                    try:
                        parse_result = NameParser(parse_method=('normal', 'anime')[show.is_anime]).parse(curResult["title"])
                        curResult["quality"] = parse_result.quality
                        curResult["release_group"] = parse_result.release_group
                        curResult["version"] = parse_result.version
                    except (InvalidNameException, InvalidShowException) as error:
                        logger.debug("{0}".format(error))
                        continue

                foundResults["results"] += searchResults

    if not didSearch:
        logger.info("Unable to find any results. Please check the log")

    # Remove provider from thread name before return results
    threading.currentThread().name = origThreadName

    foundResults["results"].sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
    return foundResults
