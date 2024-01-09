import datetime
import os
import re
import threading
import traceback
from typing import TYPE_CHECKING

import sickchill.oldbeard.name_cache
import sickchill.oldbeard.providers
from sickchill import logger, settings
from sickchill.helper.exceptions import AuthException
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.show.History import History

if TYPE_CHECKING:  # pragma: no cover
    from sickchill.oldbeard.classes import SearchResult

from . import clients, common, db, helpers, notifiers, nzbget, nzbSplitter, sab, show_name_helpers, ui
from .common import MULTI_EP_RESULT, Quality, SEASON_RESULT, SNATCHED, SNATCHED_BEST, SNATCHED_PROPER


def _download_result(result: "SearchResult"):
    """
    Downloads a result to the appropriate black hole folder.

    :param result: SearchResult instance to download.
    :return: boolean, True on success
    """

    result_was_downloaded = False

    result_provider = result.provider
    if result_provider is None:
        logger.exception("Invalid provider name - this is a coding error, report it please")
        return result_was_downloaded

    # nzbs/torrents with a URL can just be downloaded from the provider
    if result.is_torrent or result.is_nzb:
        result_was_downloaded = result_provider.download_result(result)
    # if it's an nzb data result
    elif result.is_nzbdata:
        # get the final file path to the nzb
        filename = os.path.join(settings.NZB_DIR, f"{result.name}.nzb")
        logger.info(f"Saving NZB to {filename}")

        # save the data to disk
        try:
            with open(filename, "w") as fileOut:
                fileOut.write(result.extraInfo[0])

            result_was_downloaded = True
            helpers.chmodAsParent(filename)

        except EnvironmentError as error:
            logger.exception(f"Error trying to save NZB to black hole: {error}")
            result_was_downloaded = False
    else:
        logger.exception("Invalid provider type - this is a coding error, report it please")
        result_was_downloaded = False

    return result_was_downloaded


def snatch_episode(result: "SearchResult", end_status=SNATCHED):
    """
    Contains the internal logic necessary to actually "snatch" a result that
    has been found.

    :param result: SearchResult instance to be snatched.
    :param end_status: the episode status that should be used for the episode object once it's snatched.
    :return: boolean, True on success
    """

    if result is None:
        return False

    if settings.ALLOW_HIGH_PRIORITY:
        # if it aired recently make it high priority
        for episode in result.episodes:
            if datetime.date.today() - episode.airdate <= datetime.timedelta(days=7):
                result.priority = 1

    end_status = SNATCHED_PROPER if re.search(r"\b(proper|repack|real)\b", result.name, re.I) else end_status

    # Torrents can be sent to clients or saved to disk
    if result.is_torrent:
        # torrents are saved to disk when blackhole mode
        if settings.TORRENT_METHOD == "blackhole":
            snatched_result = _download_result(result)
        else:
            if not result.content and not result.url.startswith("magnet"):
                if result.provider.login():
                    result.content = result.provider.get_url(result.url, returns="content")

            if result.content or result.url.startswith("magnet"):
                client = clients.getClientInstance(settings.TORRENT_METHOD)()
                snatched_result = client.sendTORRENT(result)
            else:
                logger.warning("Torrent file content is empty")
                # TODO: This is broken!!
                # History().log_failed(result.episodes, result.name, result.provider)
                History().log_failed(result.episodes[0], result.name, result.provider.name)  # This one seems to work
                snatched_result = False
    # NZBs can be sent straight to SAB or saved to disk
    elif result.is_nzb or result.is_nzbdata:
        if settings.NZB_METHOD == "blackhole":
            snatched_result = _download_result(result)
        elif settings.NZB_METHOD == "sabnzbd":
            snatched_result = sab.send_nzb(result)
        elif settings.NZB_METHOD == "nzbget":
            is_proper = True if end_status == SNATCHED_PROPER else False
            snatched_result = nzbget.send_nzb(result, is_proper)
        elif settings.NZB_METHOD == "download_station":
            client = clients.getClientInstance(settings.NZB_METHOD)(settings.SYNOLOGY_DSM_HOST, settings.SYNOLOGY_DSM_USERNAME, settings.SYNOLOGY_DSM_PASSWORD)
            snatched_result = client.send_nzb(result)
        else:
            logger.exception(f"Unknown NZB action specified in config: {settings.NZB_METHOD}")
            snatched_result = False
    else:
        logger.exception(f"Unknown result type, unable to download it ({result.result_type})")
        snatched_result = False

    if not snatched_result:
        return False

    ui.notifications.message("Episode snatched", result.name)
    History().log_snatch(result)

    # don't notify when we re-download an episode
    sql_l = []
    trakt_data = []
    for current_episode in result.episodes:
        with current_episode.lock:
            if is_first_best_match(result):
                current_episode.status = Quality.compositeStatus(SNATCHED_BEST, result.quality)
            else:
                current_episode.status = Quality.compositeStatus(end_status, result.quality)

            sql_l.append(current_episode.get_sql())

        if current_episode.status not in Quality.DOWNLOADED:
            # noinspection PyBroadException
            try:
                notifiers.notify_snatch(f"{current_episode.naming_pattern('%SN - %Sx%0E - %EN - %QN')} from {result.provider.name}")
            except Exception:
                # Without this, when notification fail, it crashes the snatch thread and SC will
                # keep snatching until notification is sent
                logger.debug("Failed to send snatch notification")

            trakt_data.append((current_episode.season, current_episode.episode))

    data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)

    if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
        logger.debug(f"Add episodes, showid: indexerid {result.show.indexerid}, Title {result.show.name} to Traktv Watchlist")
        if data:
            notifiers.trakt_notifier.update_watchlist(result.show, data_episode=data, update="add")

    if sql_l:
        main_db_con = db.DBConnection()
        main_db_con.mass_action(sql_l)

    return True


def pick_best_result(results, show):
    """
    Find the best result out of a list of search results for a show

    :param results: list of result objects
    :param show: Shows we check for
    :return: best result object
    """
    results = results if isinstance(results, list) else [results]

    logger.debug(f"Picking the best result out of {[x.name for x in results]}")

    picked_result = None

    # order the list so that preferred releases are at the top
    results.sort(key=lambda ep: show_name_helpers.hasPreferredWords(ep.name, ep.show), reverse=True)

    # find the best result for the current episode
    for result in results:
        if show and result.show is not show:
            continue

        # build the black And white list
        if show.is_anime:
            if not show.release_groups.is_valid(result):
                continue

        logger.info(f"Quality of {result.name} is {Quality.qualityStrings[result.quality]}")

        allowed_qualities, preferred_qualities = Quality.splitQuality(show.quality)

        if result.quality not in allowed_qualities + preferred_qualities:
            logger.debug(f"{result.name} is a quality we know we don't want, rejecting it")
            continue

        if not show_name_helpers.filter_bad_releases(result.name, parse=False, show=show):
            continue

        if hasattr(result, "size"):
            if settings.USE_FAILED_DOWNLOADS and History().has_failed(result.name, result.size, result.provider.name):
                logger.info(f"{result.name} has previously failed, rejecting it")
                continue

        if not picked_result:
            picked_result = result
        elif result.quality in preferred_qualities and (picked_result.quality < result.quality or picked_result.quality not in preferred_qualities):
            picked_result = result
        elif result.quality in allowed_qualities and picked_result.quality not in preferred_qualities and picked_result.quality < result.quality:
            picked_result = result
        elif picked_result.quality == result.quality:
            if "proper" in result.name.lower() or "real" in result.name.lower() or "repack" in result.name.lower():
                logger.info(f"Preferring {result.name} (repack/proper/real over nuked)")
                picked_result = result
            elif "internal" in picked_result.name.lower() and "internal" not in result.name.lower():
                logger.info(f"Preferring {result.name} (normal instead of internal)")
                picked_result = result
            elif "xvid" in picked_result.name.lower() and "x264" in result.name.lower():
                logger.info(f"Preferring {result.name} (x264 over xvid)")
                picked_result = result

    if picked_result:
        logger.debug(f"Picked {picked_result.name} as the best")
    else:
        logger.debug("No result picked.")

    return picked_result


def is_final_result(result: "SearchResult"):
    """
    Checks if the given result is good enough quality that we can stop searching for other ones.

    :param result: quality to check
    :return: True if the result is the highest quality in both of the quality lists else False
    """

    logger.debug(f"Checking if we should keep searching after we've found {result.name}")

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


def is_first_best_match(result: "SearchResult"):
    """
    Checks if the given result is the best match and if we want to stop searching providers here.

    :param result: to check
    :return: True if the result is the best quality match else False
    """

    logger.debug(f"Checking if we should stop searching for a better quality for for episode {result.name}")

    show_obj = result.episodes[0].show

    any_qualities_, best_qualities = Quality.splitQuality(show_obj.quality)

    return result.quality in best_qualities if best_qualities else False


def wanted_episodes(show, from_date):
    """
    Get a list of episodes that we want to download
    :param show: Show these episodes are from
    :param from_date: Search from a certain date
    :return: list of wanted episodes
    """
    wanted = []
    if show.paused:
        logger.debug(f"Not checking for episodes of {show.name} because the show is paused")
        return wanted

    allowed_qualities, preferred_qualities = common.Quality.splitQuality(show.quality)
    all_qualities = list(set(allowed_qualities + preferred_qualities))

    logger.debug(f"Seeing if we need anything from {show.name}")
    con = db.DBConnection()

    sql_results = con.select(
        "SELECT status, season, episode FROM tv_episodes WHERE showid = ? AND season > 0 and airdate > ?", [show.indexerid, from_date.toordinal()]
    )

    # check through the list of statuses to see if we want any
    for result in sql_results:
        status, quality = common.Quality.splitCompositeStatus(int(result["status"] or -1))
        if status not in {common.WANTED, common.DOWNLOADED, common.SNATCHED, common.SNATCHED_PROPER}:
            continue

        if status != common.WANTED:
            if preferred_qualities:
                if quality in preferred_qualities:
                    continue
            elif quality in allowed_qualities:
                continue

        episode_object = show.getEpisode(result["season"], result["episode"])
        episode_object.wantedQuality = [i for i in all_qualities if i > quality and i != common.Quality.UNKNOWN]
        wanted.append(episode_object)

    return wanted


def search_for_needed_episodes():
    """
    Check providers for details on wanted episodes

    :return: episodes we have a search hit for
    """
    found_results = {}

    did_search = False

    show_list = settings.showList
    from_date = datetime.date.min
    episodes = []

    for curShow in show_list:
        if not curShow.paused:
            sickchill.oldbeard.name_cache.build_name_cache(curShow)
            episodes.extend(wanted_episodes(curShow, from_date))

    if not episodes:
        # nothing wanted so early out, ie: avoid whatever arbitrarily
        # complex thing a provider cache update entails, for example,
        # reading rss feeds
        logger.info("No episodes needed.")
        return list(found_results.values())

    # noinspection DuplicatedCode
    original_thread_name = threading.current_thread().name

    providers = [x for x in sickchill.oldbeard.providers.sorted_provider_list(settings.RANDOMIZE_PROVIDERS) if x.is_active and x.enable_daily and x.can_daily]
    for curProvider in providers:
        threading.current_thread().name = f"{original_thread_name} :: [{curProvider.name}]"
        curProvider.cache.update_cache()

    for curProvider in providers:
        threading.current_thread().name = f"{original_thread_name} :: [{curProvider.name}]"
        try:
            found_rss_results = curProvider.search_rss(episodes)
        except AuthException as error:
            logger.warning(f"Authentication error: {error}")
            continue
        except Exception as error:
            logger.exception(f"Error while searching {curProvider.name}, skipping: {error}")
            logger.debug(traceback.format_exc())
            continue

        did_search = True

        # pick a single result for each episode, respecting existing results
        for current_episode in found_rss_results:
            if not current_episode.show or current_episode.show.paused:
                logger.debug(f"Skipping {current_episode.pretty_name} because the show is paused ")
                continue

            best_result = pick_best_result(found_rss_results[current_episode], current_episode.show)

            # if all results were rejected move on to the next episode
            if not best_result:
                logger.debug(f"All found results for {current_episode.pretty_name} were rejected.")
                continue

            # if it's already in the list (from another provider) and the newly found quality is no better, then skip it
            if current_episode in found_results and best_result.quality <= found_results[current_episode].quality:
                continue

            found_results[current_episode] = best_result

    threading.current_thread().name = original_thread_name

    if not did_search:
        logger.info("No NZB/Torrent providers found or enabled in the sickchill config for daily searches. Please check your settings.")

    return list(found_results.values())


# noinspection PyPep8Naming
def search_providers(show, episodes, manual=False, downCurQuality=False):
    """
    Walk providers for information on shows

    :param show: Show we are looking for
    :param episodes: Episodes we hope to find
    :param manual: Boolean, is this a manual search?
    :param downCurQuality: Boolean, should we re-download currently available quality file
    :return: results for search
    """
    found_results = {}
    final_results = []

    did_search = False

    # build name cache for show
    sickchill.oldbeard.name_cache.build_name_cache(show)

    # noinspection DuplicatedCode
    original_thread_name = threading.current_thread().name

    providers = [
        x for x in sickchill.oldbeard.providers.sorted_provider_list(settings.RANDOMIZE_PROVIDERS) if x.is_active and x.can_backlog and x.enable_backlog
    ]
    for curProvider in providers:
        threading.current_thread().name = f"{original_thread_name} :: [{curProvider.name}]"
        curProvider.cache.update_cache()

    threading.current_thread().name = original_thread_name

    for curProvider in providers:
        threading.current_thread().name = f"{original_thread_name} :: [{curProvider.name}]"

        if curProvider.anime_only and not show.is_anime:
            logger.debug(f"{show.name} is not an anime, skipping")
            continue

        found_results[curProvider.name] = {}

        search_count = 0
        search_mode = curProvider.search_mode

        # Always search for episode when manually searching when in season
        if search_mode == "season" and manual is True:
            search_mode = "episode"

        while True:
            search_count += 1

            logger.info(
                _("Performing {episode_or_season} search for {show}").format(
                    episode_or_season=(_("season pack"), _("episode"))[search_mode == "episode"], show=show.name
                )
            )

            try:
                search_results = curProvider.find_search_results(show, episodes, search_mode, manual, downCurQuality)
            except AuthException as error:
                logger.warning(f"Authentication error: {error}")
                break
            except Exception as error:
                logger.exception(f"Exception while searching {curProvider.name}. Error: {error}")
                logger.debug(traceback.format_exc())
                break

            did_search = True

            if search_results:
                # make a list of all the results for this provider
                for current_episode in search_results:
                    if current_episode in found_results[curProvider.name]:
                        found_results[curProvider.name][current_episode] += search_results[current_episode]
                    else:
                        found_results[curProvider.name][current_episode] = search_results[current_episode]

                break
            elif search_count == 2 or not curProvider.search_fallback:
                break

            if search_mode == "season":
                logger.debug("Fallback episode search initiated")
                search_mode = "episode"
            else:
                logger.debug("Fallback season pack search initiate")
                search_mode = "season"

        # skip to next provider if we have no results to process
        if not found_results[curProvider.name]:
            continue

        # pick the best season NZB
        best_season_result = None
        if SEASON_RESULT in found_results[curProvider.name]:
            best_season_result = pick_best_result(found_results[curProvider.name][SEASON_RESULT], show)

        highest_quality_overall = 0
        for cur_episode in found_results[curProvider.name]:
            for cur_result in found_results[curProvider.name][cur_episode]:
                if cur_result.quality != Quality.UNKNOWN and cur_result.quality > highest_quality_overall:
                    highest_quality_overall = cur_result.quality
        logger.debug(f"The highest quality of any match is {Quality.qualityStrings[highest_quality_overall]}")

        # see if every episode is wanted
        if best_season_result:
            searched_seasons = {str(x.season) for x in episodes}

            # get the quality of the season nzb
            season_quality = best_season_result.quality
            logger.info(f"The quality of the season {best_season_result.provider.provider_type} is {Quality.qualityStrings[season_quality]}")

            main_db_con = db.DBConnection()
            all_episodes = [
                int(x["episode"])
                for x in main_db_con.select(
                    f"SELECT episode FROM tv_episodes WHERE showid = ? AND ( season IN ( {','.join(['?'] * len(searched_seasons))} ) )",
                    [show.indexerid] + list(searched_seasons),
                )
            ]

            logger.info(f"Executed query: [SELECT episode FROM tv_episodes WHERE showid = {show.indexerid} AND season in {searched_seasons}]")
            logger.debug(f"Episode list: {all_episodes}")

            all_wanted = True
            some_wanted = False
            for episode_number in all_episodes:
                for season in (x.season for x in episodes):
                    if not show.wantEpisode(season, episode_number, season_quality, downCurQuality):
                        all_wanted = False
                    else:
                        some_wanted = True

            # if we need every ep in the season and there's nothing better, then just download this and be done with it (unless single episodes are preferred)
            if all_wanted and best_season_result.quality == highest_quality_overall:
                logger.info(f"Every ep in this season is needed, downloading the whole {best_season_result.provider.provider_type} {best_season_result.name}")
                episode_objects = []
                for episode_number in all_episodes:
                    for season in {x.season for x in episodes}:
                        episode_objects.append(show.getEpisode(season, episode_number))
                best_season_result.episodes = episode_objects

                # Remove provider from thread name before return results
                threading.current_thread().name = original_thread_name

                return [best_season_result]

            elif not some_wanted:
                logger.info(f"No eps from this season are wanted at this quality, ignoring the result of {best_season_result.name}")

            else:
                if best_season_result.result_type != GenericProvider.TORRENT:
                    logger.debug("Breaking apart the NZB and adding the individual ones to our results")

                    # if not, break it apart and add them as the lowest priority results
                    split_results = nzbSplitter.split_result(best_season_result)
                    episode_number = -1
                    for current_result in split_results:
                        if len(current_result.episodes) == 1:
                            episode_number = current_result.episodes[0].episode
                        elif len(current_result.episodes) > 1:
                            episode_number = MULTI_EP_RESULT

                        if episode_number >= 0 and episode_number in found_results[curProvider.name]:
                            found_results[curProvider.name][episode_number].append(current_result)
                        else:
                            found_results[curProvider.name][episode_number] = [current_result]

                # If this is a torrent all we can do is leech the entire torrent, user will have to select which eps not do download in his torrent client
                else:
                    # Season result from Torrent Provider must be a full-season torrent, creating multi-ep result for it.
                    logger.info(
                        "Adding multi-ep result for full-season torrent. Set the episodes you don't want to 'don't download' in your torrent client if desired!"
                    )
                    episode_objects = []
                    for episode_number in all_episodes:
                        for season in {x.season for x in episodes}:
                            episode_objects.append(show.getEpisode(season, episode_number))
                    best_season_result.episodes = episode_objects

                    if MULTI_EP_RESULT in found_results[curProvider.name]:
                        found_results[curProvider.name][MULTI_EP_RESULT].append(best_season_result)
                    else:
                        found_results[curProvider.name][MULTI_EP_RESULT] = [best_season_result]

        # go through multi-ep results and see if we really want them or not, get rid of the rest
        multi_results = {}
        if MULTI_EP_RESULT in found_results[curProvider.name]:
            for _multiResult in found_results[curProvider.name][MULTI_EP_RESULT]:
                logger.debug(f"Seeing if we want to bother with multi-episode result {_multiResult.name}")

                # Filter result by ignore/required/whitelist/blacklist/quality, etc
                multi_result = pick_best_result(_multiResult, show)
                if not multi_result:
                    continue

                # see how many of the eps that this result covers aren't covered by single results
                needed_episodes = []
                unneeded_episodes = []
                for epObj in multi_result.episodes:
                    # if we have results for the episode
                    if epObj.episode in found_results[curProvider.name] and len(found_results[curProvider.name][epObj.episode]) > 0:
                        unneeded_episodes.append(epObj.episode)
                    else:
                        needed_episodes.append(epObj.episode)

                logger.debug(f"Single-ep check result is needed_episodes: {needed_episodes}, unneeded_episodes: {unneeded_episodes}")

                if not needed_episodes:
                    logger.debug("All of these episodes were covered by single episode results, ignoring this multi-episode result")
                    continue

                # check if these eps are already covered by another multi-result
                needed_multiepisodes = []
                unneeded_multiepisodes = []
                for epObj in multi_result.episodes:
                    if epObj.episode in multi_results:
                        unneeded_multiepisodes.append(epObj.episode)
                    else:
                        needed_multiepisodes.append(epObj.episode)

                logger.debug(f"Multi-ep check result is needed_multiepisodes: {needed_multiepisodes}, unneeded_multiepisodes: {unneeded_multiepisodes}")

                if not needed_multiepisodes:
                    logger.debug("All of these episodes were covered by another multi-episode nzbs, ignoring this multi-ep result")
                    continue

                # don't bother with the single result if we're going to get it with a multi result
                for epObj in multi_result.episodes:
                    multi_results[epObj.episode] = multi_result
                    if epObj.episode in found_results[curProvider.name]:
                        logger.debug(
                            "A needed multi-episode result overlaps with a single-episode result for ep #"
                            + f"{epObj.episode}"
                            + ", removing the single-episode results from the list"
                        )
                        del found_results[curProvider.name][epObj.episode]

        # of all the single ep results narrow it down to the best one for each episode
        final_results += set(multi_results.values())
        for current_episode in found_results[curProvider.name]:
            if current_episode in (MULTI_EP_RESULT, SEASON_RESULT):
                continue

            if not found_results[curProvider.name][current_episode]:
                continue

            # if all results were rejected move on to the next episode
            best_result = pick_best_result(found_results[curProvider.name][current_episode], show)
            if not best_result:
                continue

            # add result if it's not a duplicate and
            found = False
            for i, result in enumerate(final_results):
                for best_result_episode in best_result.episodes:
                    if best_result_episode in result.episodes:
                        if result.quality < best_result.quality:
                            final_results.pop(i)
                        else:
                            found = True
            if not found:
                final_results += [best_result]

        # check that we got all the episodes we wanted first before doing a match and snatch
        wanted_episode_count = 0
        for wanted_episode in episodes:
            for result in final_results:
                if wanted_episode in result.episodes and is_final_result(result):
                    wanted_episode_count += 1

        # make sure we search every provider for results unless we found everything we wanted
        if wanted_episode_count == len(episodes):
            break

    if not did_search:
        logger.info("No NZB/Torrent providers found or enabled in the sickchill config for backlog searches. Please check your settings.")

    # Remove provider from thread name before return results
    threading.current_thread().name = original_thread_name
    return final_results
