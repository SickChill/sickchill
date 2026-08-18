import datetime
import threading
import time

import sickchill
from sickchill import logger, settings
from sickchill.oldbeard import db, network_timezones, ui
from sickchill.oldbeard.network_timezones import sc_now, sc_timezone


class ShowUpdater(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

        self.seven_days = 7 * 24 * 60 * 60

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True
        try:
            logger.info("ShowUpdater for TVDB API V4 starting")

            cache_db_con = db.DBConnection("cache.db")
            for index, provider in sickchill.indexer:
                database_result = cache_db_con.select("SELECT `time` FROM lastUpdate WHERE provider = ?", [provider.name])
                last_update = int(database_result[0][0]) if database_result else 0
                network_timezones.update_network_dict()
                update_timestamp = int(time.time())
                updated_shows = []
                http_calls_note = ""
                # When True, safe to advance cache lastUpdate (successful feed or first full run)
                advance_last_update = True

                if last_update:
                    logger.info("Last update: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_update))))
                    try:
                        # V4: single since= window with pagination (no 7-day chunking required)
                        TvdbData = sickchill.indexer[1].updates(fromTime=last_update, toTime=update_timestamp)
                        TvdbData.series()
                        if not getattr(TvdbData, "feed_ok", True):
                            # Total feed failure — not the same as a successful empty change list
                            advance_last_update = False
                            updated_shows = []
                            http_calls_note = "; update feed failed (will retry same window next cycle)"
                            logger.warning("TVDB v4 update feed failed for all entity types; not advancing lastUpdate, scheduling disk refreshes only")
                        else:
                            updated_shows = [d["id"] for d in TvdbData.series]
                            http_calls_note = f"; update feed reported {len(updated_shows)} series id(s)"
                            logger.info(f"TVDB v4 update feed: {len(updated_shows)} series need refresh{http_calls_note}")
                    except Exception as error:
                        advance_last_update = False
                        updated_shows = []
                        http_calls_note = "; update feed error (will retry same window next cycle)"
                        logger.warning(
                            f"TVDB v4 updates failed ({error}); not advancing lastUpdate, "
                            f"scheduling disk refreshes only (not a forced full re-pull of all shows)"
                        )
                else:
                    logger.info(_("No last update time from the cache, so we do a full update for all shows"))

                pi_list = []
                full_updates = 0
                refreshes = 0
                skipped = 0
                full_update_names = []
                loop_completed = True

                for cur_show in settings.show_list:
                    if settings.stopping or settings.restarting:
                        loop_completed = False
                        break
                    try:
                        cur_show.next_episode()

                        skip_update = False
                        # Skip ended or paused shows until interval is reached
                        if (cur_show.status == "Ended" or cur_show.paused) and settings.ENDED_SHOWS_UPDATE_INTERVAL != 0:  # 0 is always
                            if settings.ENDED_SHOWS_UPDATE_INTERVAL == -1:  # Never update if neg 1
                                skip_update = True
                            if (
                                sc_now() - datetime.datetime.fromordinal(cur_show.last_update_indexer or 1).replace(tzinfo=sc_timezone)
                            ).days < settings.ENDED_SHOWS_UPDATE_INTERVAL:
                                skip_update = True

                        # Full indexer update when no last_update cache or show is in the v4 updated list.
                        # skip_update always wins (e.g. ENDED_SHOWS_UPDATE_INTERVAL == -1).
                        if (not last_update or (advance_last_update and cur_show.indexerid in updated_shows)) and not skip_update:
                            try:
                                cur_show.idxr.clear_episode_cache(cur_show.indexerid)
                            except Exception as error:
                                logger.debug(f"clear_episode_cache failed for {cur_show.indexerid}: {error}")
                            pi_list.append(cur_show.update(force))
                            full_updates += 1
                            full_update_names.append(getattr(cur_show, "name", None) or str(cur_show.indexerid))
                        elif not skip_update:
                            # Disk refresh only — no indexer episode re-pull
                            pi_list.append(cur_show.refresh(force))
                            refreshes += 1
                        else:
                            skipped += 1

                    except Exception as error:
                        logger.info(_("Automatic update failed: {error}").format(error=error))

                logger.info(f"ShowUpdater scheduled full updates={full_updates}, refreshes={refreshes}, skipped={skipped}{http_calls_note}")
                if full_update_names:
                    logger.debug(f"ShowUpdater full update shows: {', '.join(full_update_names)}")
                else:
                    logger.debug("ShowUpdater full update shows: (none)")

                ui.ProgressIndicators.setIndicator("dailyUpdate", ui.QueueProgressIndicator("Daily Update", pi_list))

                # Only advance lastUpdate when the feed succeeded (or first full run) AND the
                # show loop finished (not interrupted by stop/restart).
                if advance_last_update and loop_completed:
                    if database_result:
                        cache_db_con.action("UPDATE lastUpdate SET `time` = ? WHERE provider = ?", [str(update_timestamp), provider.name])
                    else:
                        cache_db_con.action("INSERT INTO lastUpdate (time, provider) VALUES (?, ?)", [str(update_timestamp), provider.name])
                elif not loop_completed:
                    logger.info(f"Preserving lastUpdate for {provider.name}: show loop interrupted")
                else:
                    logger.info(f"Preserving lastUpdate for {provider.name} after feed failure")
        except Exception as error:
            logger.exception(error)

        self.amActive = False

    @staticmethod
    def request_hook(response, **kwargs):
        logger.info(f"{response.request.method} URL: {response.request.url} [Status: {response.status_code}]")

    def __del__(self):
        pass
