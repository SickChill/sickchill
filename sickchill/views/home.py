import ast
import base64
import datetime
import json
import os
import time
import urllib.parse
from pathlib import Path
from urllib.parse import unquote_plus

import requests

import sickchill.oldbeard
from sickchill import adba, logger, settings
from sickchill.helper import try_int
from sickchill.helper.common import episode_num, pretty_file_size
from sickchill.helper.exceptions import CantUpdateShowException, NoNFOException, ShowDirectoryNotFoundException
from sickchill.oldbeard import clients, config, db, filters, helpers, notifiers, sab, search_queue, subtitles as subtitle_module, ui
from sickchill.oldbeard.blackandwhitelist import BlackAndWhiteList, short_group_names
from sickchill.oldbeard.common import cpu_presets, FAILED, IGNORED, Overview, Quality, SKIPPED, SNATCHED_BEST, statusStrings, UNAIRED, WANTED
from sickchill.oldbeard.scene_numbering import (
    get_scene_absolute_numbering,
    get_scene_absolute_numbering_for_show,
    get_scene_numbering,
    get_scene_numbering_for_show,
    get_xem_absolute_numbering_for_show,
    get_xem_numbering_for_show,
    set_scene_numbering,
)
from sickchill.oldbeard.trakt_api import TraktAPI
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.providers.metadata.helpers import getShowImage
from sickchill.show.Show import Show
from sickchill.system.Restart import Restart
from sickchill.system.Shutdown import Shutdown
from sickchill.tv import TVShow
from sickchill.update_manager import UpdateManager
from sickchill.views.common import PageTemplate
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route("/home(/?.*)", name="home")
class Home(WebRoot):
    def __init__(self, backend, back2=None):
        super().__init__(backend, back2)
        backend = None
        self.current_show = backend
        self.new_show_dir = None
        self.any_qualities = None
        self.best_qualities = None
        self.exceptions_list = None
        self.new_default_ep_status = None
        self.new_season_folders = None
        self.new_paused = None
        self.new_sports = None
        self.new_subtitles = None
        self.new_ignore_words = None
        self.new_prefer_words = None
        self.new_require_words = None
        self.new_anime = None
        self.new_scene = None
        self.new_air_by_date = None

    def _genericMessage(self, subject=None, message=None):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="home", title="")

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if not show:
            return None, _("Invalid show parameters")

        show_obj = Show.find(settings.show_list, int(show))

        if not show_obj:
            return None, _("Invalid show parameters")

        if absolute:
            episode_object = show_obj.get_episode(absolute_number=absolute)
        elif season and episode:
            episode_object = show_obj.get_episode(season, episode)
        else:
            return None, _("Invalid parameters")

        if not episode_object:
            return None, _("Episode couldn't be retrieved")

        return episode_object, ""

    def index(self):
        t = PageTemplate(rh=self, filename="home.mako")
        selected_root = self.get_body_argument("root", "")

        if selected_root and settings.ROOT_DIRS:
            backend_dirs = settings.ROOT_DIRS.split("|")[1:]
            try:
                assert selected_root != "-1"
                selected_root_dir = backend_dirs[int(selected_root)]
            except (IndexError, ValueError, TypeError, AssertionError):
                selected_root_dir = ""
        else:
            selected_root_dir = ""

        shows = []
        anime = []
        for show in settings.show_list:
            if show.get_location.startswith(selected_root_dir):
                if settings.ANIME_SPLIT_HOME and show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)

        stats = self.show_statistics()
        return t.render(
            title=_("Home"),
            header=_("Show List"),
            topmenu="home",
            sorted_show_lists=[["Shows", shows], ["Anime", anime]],
            show_stat=stats[0],
            max_download_count=stats[1],
            controller="home",
            action="index",
            selected_root=selected_root or "-1",
        )

    def filter(self):
        t = PageTemplate(rh=self, filename="home.mako")

        selected_root = self.get_body_argument("root", "")
        page = try_int(self.get_argument("p", default="0"))
        limit = try_int(self.get_argument("limit", default="0"))
        kind = self.get_argument("type", "all")
        genre = self.get_argument("genre", "")
        if kind not in ("all", "series", "anime"):
            kind = "all"

        if selected_root and settings.ROOT_DIRS:
            backend_dirs = settings.ROOT_DIRS.split("|")[1:]
            try:
                assert selected_root != "-1"
                selected_root_dir = backend_dirs[int(selected_root)]
            except (IndexError, ValueError, TypeError, AssertionError):
                selected_root_dir = ""
        else:
            selected_root_dir = ""

        shows_to_show = []
        skipped = 0
        for show in settings.show_list:
            if not show.get_location.startswith(selected_root_dir):
                continue

            if kind == "anime" and not show.is_anime:
                skipped += 1
                continue

            if kind == "series" and show.is_anime:
                skipped += 1
                continue

            if genre and genre.lower() not in show.genre:
                skipped += 1
                continue

            shows_to_show.append(show)
            if limit and len(shows_to_show) == limit:
                break

        logger.debug(f"skipped {skipped} shows due to filters: genre: {genre}, limit: {limit}, kind: {kind}")
        if limit:
            upper_slice = min(page * limit + limit, len(shows_to_show))
            lower_slice = min(page * limit, len(shows_to_show) - limit)

            number_of_pages = len(shows_to_show) // limit
            if len(shows_to_show) % limit:
                number_of_pages += 1

            logger.info(f"Split home into {number_of_pages} pages")
        else:
            upper_slice = len(shows_to_show) - 1
            lower_slice = 0

        shows = []
        anime = []
        for show in shows_to_show[lower_slice:upper_slice]:
            if settings.ANIME_SPLIT_HOME and show.is_anime:
                anime.append(show)
            else:
                shows.append(show)

        stats = self.show_statistics()
        return t.render(
            title=_("Home"),
            header=_("Show List"),
            topmenu="home",
            sorted_show_lists=[["Shows", shows], ["Anime", anime]],
            show_stat=stats[0],
            max_download_count=stats[1],
            controller="home",
            action="index",
            selected_root=selected_root or "-1",
        )

    @staticmethod
    def show_statistics():
        """Loads show and episode statistics from db"""
        main_db_con = db.DBConnection()
        today = str(datetime.date.today().toordinal())

        status_quality = "(" + ",".join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST]) + ")"
        status_download = "(" + ",".join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ")"

        sql_statement = "SELECT showid,"

        # noinspection PyPep8
        sql_statement += (
            " (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN "
            + status_quality
            + ") AS ep_snatched,"
        )
        # noinspection PyPep8
        sql_statement += (
            " (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN "
            + status_download
            + ") AS ep_downloaded,"
        )
        sql_statement += " (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1"
        sql_statement += " AND ((airdate <= " + today + " AND status IN (" + ",".join([str(SKIPPED), str(WANTED), str(FAILED)]) + "))"
        sql_statement += " OR (status IN " + status_quality + ") OR (status IN " + status_download + "))) AS ep_total,"

        sql_statement += " (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= " + today
        sql_statement += (" AND season > 0", "")[settings.DISPLAY_SHOW_SPECIALS] + " AND status IN (" + ",".join([str(UNAIRED), str(WANTED)]) + ")"
        sql_statement += " ORDER BY airdate ASC LIMIT 1) AS ep_airs_next,"

        sql_statement += " (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1"
        sql_statement += (" AND season > 0", "")[settings.DISPLAY_SHOW_SPECIALS] + f" AND status <> {UNAIRED}"
        sql_statement += " ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev,"

        # @TODO: Store each show_size in tv_shows. also change in displayShow.mako:250, where we use helpers.get_size()
        sql_statement += " (SELECT SUM(file_size) FROM tv_episodes WHERE showid=tv_eps.showid) AS show_size"
        sql_statement += " FROM tv_episodes tv_eps GROUP BY showid"

        sql_result = main_db_con.select(sql_statement)

        show_stat = {}
        max_download_count = 1000
        for cur_result in sql_result:
            show_stat[cur_result["showid"]] = cur_result
            if cur_result["ep_total"] > max_download_count:
                max_download_count = cur_result["ep_total"]

        max_download_count *= 100

        return show_stat, max_download_count

    def is_alive(self):
        callback = self.get_query_argument("callback")
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "text/javascript")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")

        if settings.started:
            return callback + "(" + json.dumps({"msg": str(settings.PID)}) + ");"

        return callback + "(" + json.dumps({"msg": "nope"}) + ");"

    @staticmethod
    def haveKODI():
        return settings.USE_KODI and settings.KODI_UPDATE_LIBRARY

    @staticmethod
    def havePLEX():
        return settings.USE_PLEX_SERVER and settings.PLEX_UPDATE_LIBRARY

    @staticmethod
    def haveEMBY():
        return settings.USE_EMBY

    @staticmethod
    def haveJELLYFIN():
        return settings.USE_JELLYFIN

    @staticmethod
    def haveTORRENT():
        host_good = (settings.TORRENT_HOST[:5] == "http:", settings.TORRENT_HOST[:5] == "https")[settings.ENABLE_HTTPS]
        if settings.USE_TORRENTS and settings.TORRENT_METHOD != "blackhole" and host_good:
            return True

        return False

    def testSABnzbd(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        username = self.get_body_argument("username")
        password = filters.unhide(settings.SAB_PASSWORD, self.get_body_argument("password"))
        apikey = filters.unhide(settings.SAB_APIKEY, self.get_body_argument("apikey"))

        host = config.clean_url(self.get_body_argument("host"))
        connection, access_msg = sab.get_sab_acces_method(host)
        if connection:
            authed, auth_msg = sab.test_client_connection(host, username, password, apikey)
            if authed:
                return _("Success. Connected and authenticated")

            return _("Authentication failed. SABnzbd expects") + " '" + access_msg + "' " + _("as authentication method") + ", '" + auth_msg + "'"

        return _("Unable to connect to host")

    @staticmethod
    def __torrent_test(host, username, password, method):
        client = clients.getClientInstance(method)
        result, message = client(host, username, password).test_client_connection()
        return message

    def testDSM(self):
        host = config.clean_url(self.get_body_argument("host"))
        username = self.get_body_argument("username")
        password = filters.unhide(settings.SYNOLOGY_DSM_PASSWORD, self.get_body_argument("password"))
        return self.__torrent_test(host, username, password, "download_station")

    def testTorrent(self):
        torrent_method = self.get_body_argument("torrent_method")
        host = config.clean_url(self.get_body_argument("host"))
        username = self.get_body_argument("username")
        password = filters.unhide(settings.TORRENT_PASSWORD, self.get_body_argument("password"))
        return self.__torrent_test(host, username, password, torrent_method)

    def testFreeMobile(self):
        freemobile_id = self.get_body_argument("freemobile_id")
        freemobile_apikey = filters.unhide(settings.FREEMOBILE_APIKEY, self.get_body_argument("freemobile_apikey"))

        result, message = notifiers.freemobile_notifier.test_notify(freemobile_id, freemobile_apikey)
        if result:
            return _("SMS sent successfully")

        return _("Problem sending SMS: {message}".format(message=message))

    def testTelegram(self):
        telegram_id = self.get_body_argument("telegram_id")
        telegram_apikey = filters.unhide(settings.TELEGRAM_APIKEY, self.get_body_argument("telegram_apikey"))
        result, message = notifiers.telegram_notifier.test_notify(telegram_id, telegram_apikey)
        if result:
            return _("Telegram notification succeeded. Check your Telegram clients to make sure it worked")

        return _("Error sending Telegram notification: {message}".format(message=message))

    def testJoin(self):
        join_id = self.get_body_argument("join_id")
        join_apikey = filters.unhide(settings.JOIN_APIKEY, self.get_body_argument("join_apikey"))

        result, message = notifiers.join_notifier.test_notify(join_id, join_apikey)
        if result:
            return _("join notification succeeded. Check your join clients to make sure it worked")

        return _("Error sending join notification: {message}".format(message=message))

    def testGrowl(self):
        host = self.get_query_argument("host")
        password = filters.unhide(settings.GROWL_PASSWORD, self.get_query_argument("password"))
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host, default_port=23053)
        result = notifiers.growl_notifier.test_notify(host, password)

        pw_append = _(" with password") + ": " + password if password else ""
        if result:
            return _("Registered and Tested growl successfully {growl_host}").format(growl_host=unquote_plus(host)) + pw_append

        return _("Registration and Testing of growl failed {growl_host}").format(growl_host=unquote_plus(host)) + pw_append

    def testProwl(self):
        prowl_api = self.get_query_argument("prowl_api")
        prowl_priority = self.get_query_argument("prowl_priority")
        result = notifiers.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return _("Test prowl notice sent successfully")

        return _("Test prowl notice failed")

    def testBoxcar2(self):
        access_token = self.get_query_argument("accesstoken")
        result = notifiers.boxcar2_notifier.test_notify(access_token)
        if result:
            return _("Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked")

        return _("Error sending Boxcar2 notification")

    def testPushover(self):
        user_key = self.get_query_argument("userKey")
        api_key = self.get_query_argument("apiKey")

        result = notifiers.pushover_notifier.test_notify(user_key, api_key)
        if result:
            return _("Pushover notification succeeded. Check your Pushover clients to make sure it worked")

        return _("Error sending Pushover notification")

    def testGotify(self):
        host = self.get_body_argument("host")
        host = config.clean_url(host)
        authorization_token = self.get_body_argument("authorizationToken")
        result, message = notifiers.gotify_notifier.test_notify(host, authorization_token)
        logger.debug(f"Gotify result: {result} {message}")
        if result:
            return _("Gotify notification succeeded. Check your Gotify clients to make sure it worked.")

        return _("Error sending Gotify notification. {message}".format(message=message))

    @staticmethod
    def twitterStep1():
        # noinspection PyProtectedMember
        return notifiers.twitter_notifier._get_authorization()

    def twitterStep2(self):
        key = self.get_query_argument("key")
        # noinspection PyProtectedMember
        result = notifiers.twitter_notifier._get_credentials(key)
        logger.info(f"result: {result}")
        if result:
            return _("Key verification successful")

        return _("Unable to verify key")

    @staticmethod
    def testTwitter():
        result = notifiers.twitter_notifier.test_notify()
        if result:
            return _("Tweet successful, check your twitter to make sure it worked")

        return _("Error sending tweet")

    @staticmethod
    def testTwilio():
        # if not notifiers.twilio_notifier.account_regex.match(settings.TWILIO_ACCOUNT_SID):
        #     return _("Please enter a valid account sid")
        #
        # if not notifiers.twilio_notifier.auth_regex.match(settings.TWILIO_AUTH_TOKEN):
        #     return _("Please enter a valid auth token")
        #
        # if not notifiers.twilio_notifier.phone_regex.match(settings.TWILIO_PHONE_SID):
        #     return _("Please enter a valid phone sid")
        #
        # if not notifiers.twilio_notifier.number_regex.match(settings.TWILIO_TO_NUMBER):
        #     return _('Please format the phone number as "+1-###-###-####"')
        #
        # result = notifiers.twilio_notifier.test_notify()
        # if result:
        #     return _("Authorization successful and number ownership verified")
        # else:
        return _("Error sending sms")

    @staticmethod
    def testSlack():
        result = notifiers.slack_notifier.test_notify()
        if result:
            return _("Slack message successful")

        return _("Slack message failed")

    @staticmethod
    def testMattermost():
        result = notifiers.mattermost_notifier.test_notify()
        if result:
            return _("Mattermost message successful")

        return _("Mattermost message failed")

    @staticmethod
    def testMattermostBot():
        result = notifiers.mattermostbot_notifier.test_notify()
        if result:
            return _("Mattermost Bot message successful")

        return _("Mattermost Bot message failed")

    @staticmethod
    def testRocketChat():
        result = notifiers.rocketchat_notifier.test_notify()
        if result:
            return _("Rocket.Chat message successful")

        return _("Rocket.Chat message failed")

    @staticmethod
    def testMatrix():
        result = notifiers.matrix_notifier.test_notify()
        if result:
            return _("Matrix message successful")

        return _("Matrix message failed")

    def testDiscord(self):
        webhook = self.get_body_argument("webhook")
        name = self.get_body_argument("name")
        avatar = self.get_body_argument("avatar")
        tts = self.get_body_argument("tts")

        if GenericProvider.invalid_url(webhook):
            return _("Invalid URL for webhook")

        result = notifiers.discord_notifier.test_notify(webhook, name, avatar, tts)
        if result:
            return _("Discord message successful")

        return _("Discord message failed")

    def testKODI(self):
        username = self.get_query_argument("username")
        host = config.clean_hosts(self.get_query_argument("host"))
        password = filters.unhide(settings.KODI_PASSWORD, self.get_query_argument("password"))

        results = notifiers.kodi_notifier.test_notify(unquote_plus(host), username, password)
        final_results = [
            _("Test KODI notice {result} to {kodi_host}").format(kodi_host=host, result=("failed", "sent successfully")[result])
            for host, result in results.items()
        ]

        return "<br>\n".join(final_results)

    def testPHT(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")

        username = self.get_query_argument("username")
        host = config.clean_hosts(self.get_query_argument("host"))
        password = filters.unhide(settings.PLEX_CLIENT_PASSWORD, self.get_query_argument("password"))

        final_result = ""
        for cur_host in [x.strip() for x in host.split(",")]:
            cur_result = notifiers.plex_notifier.test_notify_pht(unquote_plus(cur_host), username, password)
            if len(cur_result.split(":")) > 2 and "OK" in cur_result.split(":")[2]:
                final_result += _("Successful test notice sent to Plex Home Theater ... {plex_clients}").format(plex_clients=unquote_plus(cur_host))
            else:
                final_result += _("Test failed for Plex Home Theater ... {plex_clients}").format(plex_clients=unquote_plus(cur_host))
            final_result += "<br>" + "\n"

        ui.notifications.message(_("Tested Plex Home Theater(s)") + ":", unquote_plus(host.replace(",", ", ")))

        return final_result

    def testPMS(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")

        username = self.get_query_argument("username")
        host = config.clean_hosts(self.get_query_argument("host"))
        password = filters.unhide(settings.PLEX_SERVER_PASSWORD, self.get_query_argument("password"))
        plex_server_token = self.get_query_argument("plex_server_token")

        final_result = ""

        cur_result = notifiers.plex_notifier.test_notify_pms(unquote_plus(host), username, password, plex_server_token)
        if cur_result is None:
            final_result += _("Successful test of Plex Media Server(s) ... {plex_servers}").format(plex_servers=unquote_plus(host.replace(",", ", ")))
        elif cur_result is False:
            final_result += _("Test failed, No Plex Media Server host specified")
        else:
            final_result += _("Test failed for Plex Media Server(s) ... {plex_servers}").format(plex_servers=unquote_plus(str(cur_result).replace(",", ", ")))
        final_result += "<br>" + "\n"

        ui.notifications.message(_("Tested Plex Media Server host(s)") + ":", unquote_plus(host.replace(",", ", ")))

        return final_result

    @staticmethod
    def testLibnotify():
        if notifiers.libnotify_notifier.test_notify():
            return _("Tried sending desktop notification via libnotify")
        return notifiers.libnotify_notifier.diagnose()

    def testEMBY(self):
        host = config.clean_url(self.get_query_argument("host"))
        emby_apikey = filters.unhide(settings.EMBY_APIKEY, self.get_query_argument("emby_apikey"))
        result = notifiers.emby_notifier.test_notify(host, emby_apikey)
        if result:
            return _("Test notice sent successfully to {emby_host}").format(emby_host=unquote_plus(host))

        return _("Test notice failed to {emby_host}").format(emby_host=unquote_plus(host))

    def testJELLYFIN(self):
        host = config.clean_url(self.get_query_argument("host"))
        jellyfin_apikey = filters.unhide(settings.JELLYFIN_APIKEY, self.get_query_argument("jellyfin_apikey"))
        result = notifiers.jellyfin_notifier.test_notify(host, jellyfin_apikey)
        if result:
            return _("Test notice sent successfully to {jellyfin_host}").format(jellyfin_host=unquote_plus(host))

        return _("Test notice failed to {jellyfin_host}").format(jellyfin_host=unquote_plus(host))

    def testNMJ(self):
        host = config.clean_host(self.get_body_argument("host"))
        database = self.get_body_argument("database")
        mount = self.get_body_argument("mount")

        result = notifiers.nmj_notifier.test_notify(unquote_plus(host), database, mount)
        if result:
            return _("Successfully started the scan update")

        return _("Test failed to start the scan update")

    def settingsNMJ(self):
        host = config.clean_host(self.get_body_argument("host"))
        result = notifiers.nmj_notifier.notify_settings(unquote_plus(host))
        if result:
            return '{{"message": _("Got settings from {host}"), "database": "{database}", "mount": "{mount}"}}'.format(
                **{"host": host, "database": settings.NMJ_DATABASE, "mount": settings.NMJ_MOUNT}
            )

        # noinspection PyPep8
        return '{"message": _("Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)"), "database": "", "mount": ""}'

    def testNMJv2(self):
        host = config.clean_host(self.get_body_argument("host"))
        result = notifiers.nmjv2_notifier.test_notify(unquote_plus(host))
        if result:
            return _("Test notice sent successfully to {nmj2_host}").format(nmj2_host=unquote_plus(host))

        return _("Test notice failed to {nmj2_host}").format(nmj2_host=unquote_plus(host))

    def settingsNMJv2(self):
        host = config.clean_host(self.get_body_argument("host"))
        dbloc = self.get_body_argument("dbloc")
        instance = self.get_body_argument("instance")
        result = notifiers.nmjv2_notifier.notify_settings(unquote_plus(host), dbloc, instance)
        if result:
            return '{{"message": _("NMJ Database found at: {host}"), "database": "{database}"}}'.format(**{"host": host, "database": settings.NMJv2_DATABASE})

        # noinspection PyPep8
        return '{{"message": _("Unable to find NMJ Database at location: {dbloc}. Is the right location selected and PCH running?"), "database": ""}}'.format(
            **{"dbloc": dbloc}
        )

    def getTraktToken(self):
        trakt_pin = self.get_body_argument("trakt_pin")
        trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return _("Trakt Authorized")
        return _("Trakt Not Authorized!")

    def testTrakt(self):
        username = self.get_body_argument("username")
        blacklist_name = self.get_body_argument("blacklist_name")
        return notifiers.trakt_notifier.test_notify(username, blacklist_name)

    def testFlareSolverr(self):
        uri = self.get_body_argument("flaresolverr_uri")
        logger.debug(_("Checking flaresolverr uri: {uri}").format(uri=uri))
        try:
            requests.head(uri, timeout=30)
            result = _("Successfully connected to flaresolverr, this is experimental!")
        except (requests.ConnectionError, requests.RequestException):
            result = _("Failed to connect to flaresolverr")

        logger.debug(_("Flaresolverr result: {result}").format(result=result))
        return result

    @staticmethod
    def loadShowNotifyLists():
        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT indexer_id, show_name, notify_list FROM tv_shows ORDER BY show_name")

        data = {}
        for r in rows:
            notify_list = {"emails": "", "prowlAPIs": ""}
            if r["notify_list"] and len(r["notify_list"]) > 0:
                # First, handle legacy format (emails only)
                if not r["notify_list"][0] == "{":
                    notify_list["emails"] = r["notify_list"]
                else:
                    notify_list = dict(ast.literal_eval(r["notify_list"]))

            data[r["indexer_id"]] = {
                "id": r["indexer_id"],
                "name": r["show_name"],
                "list": notify_list["emails"],
                "prowl_notify_list": notify_list["prowlAPIs"],
            }
        data["_size"] = len(data)
        return json.dumps(data)

    def saveShowNotifyList(self):
        show = self.get_body_argument("show")
        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT indexer_id, notify_list FROM tv_shows WHERE indexer_id = ?", [show])
        # Get existing data from db for both email and prowl
        data = {}

        for r in rows:
            notify_list = {"emails": "", "prowlAPIs": ""}
            if r["notify_list"] and len(r["notify_list"]) > 0:
                # First, handle legacy format (emails only)
                if not r["notify_list"][0] == "{":
                    notify_list["emails"] = r["notify_list"]
                else:
                    notify_list = dict(ast.literal_eval(r["notify_list"]))
            data = {"id": r["indexer_id"], "email_list": notify_list["emails"], "prowl_list": notify_list["prowlAPIs"]}

        show_email = data["email_list"]
        show_prowl = data["prowl_list"]

        # Change email or prowl with new or keep the existing
        emails = self.get_body_argument("emails", show_email)
        prowl_apis = self.get_body_argument("prowlAPIs", show_prowl)

        entries = {"emails": emails, "prowlAPIs": prowl_apis}

        # TODO: Split emails and do validators.email
        if emails or prowl_apis:
            result = main_db_con.action("UPDATE tv_shows SET notify_list = ? WHERE indexer_id = ?", [str(entries), show])
        else:
            result = main_db_con.action("UPDATE tv_shows SET notify_list = Null WHERE indexer_id = ?", [show])

        if not result:
            return "ERROR"
        return "OK"

    def testEmail(self):
        port = self.get_body_argument("port")
        smtp_from = self.get_body_argument("smtp_from")
        use_tls = self.get_body_argument("use_tls")
        user = self.get_body_argument("user")
        pwd = filters.unhide(settings.EMAIL_PASSWORD, self.get_body_argument("pwd"))
        to = self.get_body_argument("to")

        host = config.clean_host(self.get_body_argument("host"))

        if notifiers.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return _("Test email sent successfully! Check inbox.")

        return _("ERROR: {last_error}").format(last_error=notifiers.email_notifier.last_err)

    def testPushalot(self):
        authorization_token = self.get_body_argument("authorizationToken")
        result = notifiers.pushalot_notifier.test_notify(authorization_token)
        if result:
            return _("Pushalot notification succeeded. Check your Pushalot clients to make sure it worked")

        return _("Error sending Pushalot notification")

    def testPushbullet(self):
        api = self.get_body_argument("api")
        result = notifiers.pushbullet_notifier.test_notify(api)
        if result:
            return _("Pushbullet notification succeeded. Check your device to make sure it worked")

        return _("Error sending Pushbullet notification")

    def getPushbulletDevices(self):
        api = self.get_body_argument("api")
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.get_devices(api)
        if result:
            return result

        return _("Error sending Pushbullet notification")

    def getPushbulletChannels(self):
        api = self.get_body_argument("api")
        result = notifiers.pushbullet_notifier.get_channels(api)
        if result:
            return result

        return _("Error sending Pushbullet notification")

    def status(self):
        tvdir_free = helpers.disk_usage_hr(settings.TV_DOWNLOAD_DIR)
        root_dir = {}

        if settings.ROOT_DIRS:
            backend_dirs = settings.ROOT_DIRS.split("|")[1:]
        else:
            backend_dirs = []

        if backend_dirs:
            for subject in backend_dirs:
                root_dir[subject] = helpers.disk_usage_hr(subject)

        t = PageTemplate(rh=self, filename="status.mako")
        return t.render(
            title=_("Status"),
            header=_("Status"),
            topmenu="system",
            tvdirFree=tvdir_free,
            rootDir=root_dir,
            controller="home",
            action="status",
        )

    def shutdown(self):
        pid = self.get_query_argument("pid")
        if not Shutdown.stop(pid):
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

        title = "Shutting down"
        message = "SickChill is shutting down..."

        return self._genericMessage(title, message)

    def restart(self):
        pid = self.get_query_argument("pid")
        if not Restart.restart(pid):
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

        t = PageTemplate(rh=self, filename="restart.mako")

        return t.render(
            title=_("Home"),
            header=_("Restarting SickChill"),
            topmenu="system",
            controller="home",
            action="restart",
        )

    def updateCheck(self):
        pid = self.get_query_argument("pid")
        if settings.DISABLE_UPDATER or str(pid) != str(settings.PID):
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

        settings.versionCheckScheduler.action.check_for_new_version(force=True)
        settings.versionCheckScheduler.action.check_for_new_news()

        return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    def update(self, pid):
        if settings.DISABLE_UPDATER or str(pid) != str(settings.PID):
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

        updater = UpdateManager()
        if updater.backup():
            if updater.update():
                # do a hard restart
                settings.events.put(settings.events.SystemEvent.RESTART)

                t = PageTemplate(rh=self, filename="restart.mako")
                return t.render(
                    title=_("Home"),
                    header=_("Restarting SickChill"),
                    topmenu="home",
                    controller="home",
                    action="restart",
                )

            return self._genericMessage(_("Update Failed"), _("Update wasn't successful, not restarting. Check your log for more information."))

        return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    @staticmethod
    def compare_db_version():
        update_manager = UpdateManager()
        db_status = update_manager.compare_db_version()

        if db_status == "upgrade":
            logger.debug("New version has a new DB version - Upgrade")
            return json.dumps({"status": "success", "message": "upgrade"})
        elif db_status == "equal":
            logger.debug("New version has the same DB version - Equal")
            return json.dumps({"status": "success", "message": "equal"})
        elif db_status == "downgrade":
            logger.debug("New version has an old DB version - Downgrade")
            return json.dumps({"status": "success", "message": "downgrade"})

        logger.exception("Couldn't compare DB version.")
        return json.dumps({"status": "error", "message": "General exception"})

    def displayShow(self):
        show = self.get_query_argument("show")

        # todo: add more comprehensive show validation
        try:
            show_obj = Show.find(settings.show_list, int(show))
        except (ValueError, TypeError):
            return self._genericMessage(_("Error"), _("Invalid show ID: {show}").format(show=str(show)))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        main_db_con = db.DBConnection()
        season_results = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC", [show_obj.indexerid]
        )

        min_season = (1, 0)[settings.DISPLAY_SHOW_SPECIALS]

        sql_results = main_db_con.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season >= ? ORDER BY season DESC, episode DESC", [show_obj.indexerid, min_season]
        )

        t = PageTemplate(rh=self, filename="displayShow.mako")
        submenu = [{"title": _("Edit"), "path": f"home/editShow?show={show_obj.indexerid}", "icon": "fa fa-pencil"}]

        try:
            show_location = (show_obj.location, True)
        except ShowDirectoryNotFoundException:
            show_location = (show_obj.get_location, False)

        show_message = ""

        if settings.showQueueScheduler.action.is_being_added(show_obj):
            show_message = _("This show is in the process of being downloaded - the info below is incomplete.")

        elif settings.showQueueScheduler.action.is_being_updated(show_obj):
            show_message = _("The information on this page is in the process of being updated.")

        elif settings.showQueueScheduler.action.is_being_refreshed(show_obj):
            show_message = _("The episodes below are currently being refreshed from disk")

        elif settings.showQueueScheduler.action.is_being_subtitled(show_obj):
            show_message = _("Currently downloading subtitles for this show")

        elif settings.showQueueScheduler.action.is_in_refresh_queue(show_obj):
            show_message = _("This show is queued to be refreshed.")

        elif settings.showQueueScheduler.action.is_in_update_queue(show_obj):
            show_message = _("This show is queued and awaiting an update.")

        elif settings.showQueueScheduler.action.is_in_subtitle_queue(show_obj):
            show_message = _("This show is queued and awaiting subtitles download.")

        if not settings.showQueueScheduler.action.is_being_added(show_obj):
            if not settings.showQueueScheduler.action.is_being_updated(show_obj):
                if show_obj.paused:
                    submenu.append({"title": _("Resume"), "path": f"home/togglePause?show={show_obj.indexerid}", "icon": "fa fa-play"})
                else:
                    submenu.append({"title": _("Pause"), "path": f"home/togglePause?show={show_obj.indexerid}", "icon": "fa fa-pause"})

                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Remove"),
                        "path": f"home/deleteShow?show={show_obj.indexerid}",
                        "class": "removeshow",
                        "confirm": True,
                        "icon": "fa fa-trash",
                    }
                )
                submenu.append({"title": _("Re-scan files"), "path": f"home/refreshShow?show={show_obj.indexerid}&amp;force=1", "icon": "fa fa-refresh"})
                # noinspection PyPep8
                submenu.append({"title": _("Force Full Update"), "path": f"home/updateShow?show={show_obj.indexerid}&amp;force=1", "icon": "fa fa-exchange"})
                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Update show in KODI"),
                        "path": f"home/updateKODI?show={show_obj.indexerid}",
                        "requires": self.haveKODI(),
                        "icon": "menu-icon-kodi",
                    }
                )
                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Update show in Emby"),
                        "path": f"home/updateEMBY?show={show_obj.indexerid}",
                        "requires": self.haveEMBY(),
                        "icon": "menu-icon-emby",
                    }
                )
                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Update show in Jellyfin"),
                        "path": f"home/updateJELLYFIN?show={show_obj.indexerid}",
                        "requires": self.haveJELLYFIN(),
                        "icon": "menu-icon-jellyfin",
                    }
                )
                if season_results and int(season_results[-1]["season"]) == 0:
                    if settings.DISPLAY_SHOW_SPECIALS:
                        # noinspection PyPep8
                        submenu.append(
                            {
                                "title": _("Hide specials"),
                                "path": f"home/toggleDisplayShowSpecials/?show={show_obj.indexerid}",
                                "confirm": True,
                                "icon": "fa fa-times",
                            }
                        )
                    else:
                        # noinspection PyPep8
                        submenu.append(
                            {
                                "title": _("Show specials"),
                                "path": f"home/toggleDisplayShowSpecials/?show={show_obj.indexerid}",
                                "confirm": True,
                                "icon": "fa fa-check",
                            }
                        )

                submenu.append({"title": _("Preview Rename"), "path": f"home/testRename?show={show_obj.indexerid}", "icon": "fa fa-tag"})

                if settings.USE_SUBTITLES and show_obj.subtitles and not settings.showQueueScheduler.action.is_being_subtitled(show_obj):
                    # noinspection PyPep8
                    submenu.append({"title": _("Download Subtitles"), "path": f"home/subtitleShow?show={show_obj.indexerid}", "icon": "fa fa-language"})

        ep_counts = {
            Overview.SKIPPED: 0,
            Overview.WANTED: 0,
            Overview.QUAL: 0,
            Overview.GOOD: 0,
            Overview.UNAIRED: 0,
            Overview.SNATCHED: 0,
            Overview.SNATCHED_PROPER: 0,
            Overview.SNATCHED_BEST: 0,
        }
        episode_categories = {}

        for current_result in sql_results:
            current_episode_category = show_obj.get_overview(current_result["status"])
            if current_episode_category:
                episode_categories[str(current_result["season"]) + "x" + str(current_result["episode"])] = current_episode_category
                ep_counts[current_episode_category] += 1

        shows = []
        anime = []
        for show in settings.show_list:
            if settings.ANIME_SPLIT_HOME and show.is_anime:
                anime.append(show)
            else:
                shows.append(show)

        bwl = None
        if show_obj.is_anime:
            bwl = show_obj.release_groups

        show_obj.exceptions = sickchill.oldbeard.scene_exceptions.get_scene_exceptions(show_obj.indexerid)

        indexerid = int(show_obj.indexerid)
        indexer = int(show_obj.indexer)

        # Delete any previous occurrences
        for index, recentShow in enumerate(settings.SHOWS_RECENT):
            if recentShow["indexerid"] == indexerid:
                del settings.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del settings.SHOWS_RECENT[4:]

        # Insert most recent show
        settings.SHOWS_RECENT.insert(
            0,
            {
                "indexerid": indexerid,
                "name": show_obj.name,
            },
        )

        return t.render(
            submenu=submenu,
            show_location=show_location,
            show_message=show_message,
            show=show_obj,
            sql_results=sql_results,
            seasonResults=season_results,
            sorted_show_lists=[["Shows", shows], ["Anime", anime]],
            bwl=bwl,
            ep_counts=ep_counts,
            epCats=episode_categories,
            all_scene_exceptions=show_obj.exceptions,
            scene_numbering=get_scene_numbering_for_show(indexerid, indexer),
            xem_numbering=get_xem_numbering_for_show(indexerid, indexer),
            scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexerid, indexer),
            xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexerid, indexer),
            title=show_obj.name,
            controller="home",
            action="displayShow",
        )

    def plotDetails(self):
        show = self.get_query_argument("show")
        season = self.get_query_argument("season")
        episode = self.get_query_argument("episode")
        main_db_con = db.DBConnection()
        result = main_db_con.select_one(
            "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", (int(show), int(season), int(episode))
        )
        return result["description"] if result else "Episode not found."

    def sceneExceptions(self):
        show = try_int(self.get_query_argument("show"))
        exeptions_list = sickchill.oldbeard.scene_exceptions.get_all_scene_exceptions(show)
        if not exeptions_list:
            return _("No scene exceptions")

        out = []
        for season, exceptions in iter(sorted(exeptions_list.items())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(exceptions.names))
        return "<br>".join(out)

    # noinspection PyUnboundLocalVariable
    def editShow(self, direct_call=False):
        if direct_call is False:
            show_id = self.get_query_argument("show", default=None)
            location = self.get_body_argument("location", default=None)
            any_qualities = self.get_body_arguments("anyQualities")
            best_qualities = self.get_body_arguments("bestQualities")
            season_folders = config.checkbox_to_value(self.get_body_argument("season_folders", default="False"))
            if show_id is None:
                show_id = self.get_body_argument("show")
                blacklist = self.get_body_argument("blacklist", default=None)
                whitelist = self.get_body_argument("whitelist", default=None)
                default_ep_status = self.get_body_argument("defaultEpStatus", default=None)
                dvdorder = config.checkbox_to_value(self.get_body_argument("dvdorder", default="False"))
                exceptions_list = self.get_body_argument("exceptions_list", default=None)
                rls_ignore_words = self.get_body_argument("rls_ignore_words", default=None)
                rls_prefer_words = self.get_body_argument("rls_prefer_words", default=None)
                rls_require_words = self.get_body_argument("rls_require_words", default=None)
                paused = config.checkbox_to_value(self.get_body_argument("paused", default="False"))
                air_by_date = config.checkbox_to_value(self.get_body_argument("air_by_date", default="False"))
                scene = config.checkbox_to_value(self.get_body_argument("scene", default="False"))
                sports = config.checkbox_to_value(self.get_body_argument("sports", default="False"))
                anime = config.checkbox_to_value(self.get_body_argument("anime", default="False"))
                subtitles = config.checkbox_to_value(self.get_body_argument("subtitles", default="False"))
        else:
            show_id = self.current_show
            location = self.new_show_dir
            any_qualities = self.any_qualities
            best_qualities = self.best_qualities
            exceptions_list = self.exceptions_list
            default_ep_status = self.new_default_ep_status
            season_folders = self.new_season_folders
            paused = self.new_paused
            sports = self.new_sports
            subtitles = self.new_subtitles
            rls_ignore_words = self.new_ignore_words
            rls_prefer_words = self.new_prefer_words
            rls_require_words = self.new_require_words
            anime = self.new_anime
            scene = self.new_scene
            air_by_date = self.new_air_by_date

        anidb_failed = False

        error, show_obj = Show.validate_indexer_id(show_id)
        if error:
            if direct_call:
                return [error]

            return self._genericMessage(_("Error"), error)

        if not show_obj:
            error_string = _("Unable to find the specified show") + f": {show_id}"
            if direct_call:
                return [error_string]

            return self._genericMessage(_("Error"), error_string)

        show_obj.exceptions = sickchill.oldbeard.scene_exceptions.get_all_scene_exceptions(show_obj.indexerid)

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC", [show_obj.indexerid]
        )

        if not (location or any_qualities or best_qualities or season_folders):
            t = PageTemplate(rh=self, filename="editShow.mako")
            groups = []

            if show_obj.is_anime:
                whitelist = show_obj.release_groups.whitelist
                blacklist = show_obj.release_groups.blacklist

                if helpers.set_up_anidb_connection() and not anidb_failed:
                    try:
                        anime = adba.Anime(settings.ADBA_CONNECTION, name=show_obj.name, cache_dir=Path(settings.CACHE_DIR))
                        groups = anime.get_groups()
                    except Exception as error:
                        ui.notifications.error(_("Unable to retrieve Fansub Groups from AniDB."))
                        logger.debug(f"Unable to retrieve Fansub Groups from AniDB. Error is {error}")

            if show_obj.is_anime:
                return t.render(
                    show=show_obj,
                    scene_exceptions=show_obj.exceptions,
                    seasonResults=seasonResults,
                    groups=groups,
                    whitelist=whitelist,
                    blacklist=blacklist,
                    title=_("Edit Show"),
                    header=_("Edit Show"),
                    controller="home",
                    action="editShow",
                )

            return t.render(
                show=show_obj,
                scene_exceptions=show_obj.exceptions,
                seasonResults=seasonResults,
                title=_("Edit Show"),
                header=_("Edit Show"),
                controller="home",
                action="editShow",
            )

        banner = self.get_body_argument("banner", default=None)
        fanart = self.get_body_argument("fanart", default=None)
        poster = self.get_body_argument("poster", default=None)
        indexer_lang = self.get_body_argument("indexerLang", default=None)
        custom_name = self.get_body_argument("custom_name", default="")
        subtitles_sc_metadata = config.checkbox_to_value(self.get_body_argument("subtitles_sc_metadata", default="False"))

        if not indexer_lang or indexer_lang not in show_obj.idxr.languages:
            indexer_lang = show_obj.lang

        # if we changed the language then kick off an update
        do_update = indexer_lang != show_obj.lang
        do_update_scene_numbering = scene != show_obj.scene or anime != show_obj.anime

        if not any_qualities:
            any_qualities = []

        if not best_qualities:
            best_qualities = []

        if not exceptions_list:
            exceptions_list = []

        if not isinstance(any_qualities, list):
            any_qualities = [any_qualities]

        if not isinstance(best_qualities, list):
            best_qualities = [best_qualities]

        if isinstance(exceptions_list, list):
            if exceptions_list:
                exceptions_list = exceptions_list[0]
            else:
                exceptions_list = None

        # Map custom exceptions
        exceptions = {}

        if exceptions_list:
            # noinspection PyUnresolvedReferences
            for season in exceptions_list.split(","):
                season, shows = season.split(":")

                show_list = []

                for cur_show in shows.split("|"):
                    show_list.append({"show_name": unquote_plus(cur_show), "custom": True})

                exceptions[int(season)] = show_list

        show_obj.custom_name = custom_name

        metadata_generator = GenericMetadata()

        def get_images(image):
            if image.startswith("data:image"):
                start = image.index("base64,") + 7
                _img_data = base64.b64decode(image[start:])
                return _img_data, _img_data

            image_parts = image.split("|")
            _img_data = getShowImage(image_parts[0])
            if len(image_parts) > 1:
                return _img_data, getShowImage(image_parts[1])

            return _img_data, _img_data

        if poster:
            img_data, img_thumb_data = get_images(poster)
            dest_path = settings.IMAGE_CACHE.poster_path(show_obj.indexerid)
            dest_thumb_path = settings.IMAGE_CACHE.poster_thumb_path(show_obj.indexerid)
            # noinspection PyProtectedMember
            metadata_generator._write_image(img_data, dest_path, overwrite=True)
            # noinspection PyProtectedMember
            metadata_generator._write_image(img_thumb_data, dest_thumb_path, overwrite=True)
        if banner:
            img_data, img_thumb_data = get_images(banner)
            dest_path = settings.IMAGE_CACHE.banner_path(show_obj.indexerid)
            dest_thumb_path = settings.IMAGE_CACHE.banner_thumb_path(show_obj.indexerid)
            # noinspection PyProtectedMember
            metadata_generator._write_image(img_data, dest_path, overwrite=True)
            # noinspection PyProtectedMember
            metadata_generator._write_image(img_thumb_data, dest_thumb_path, overwrite=True)
        if fanart:
            img_data, img_thumb_data = get_images(fanart)
            dest_path = settings.IMAGE_CACHE.fanart_path(show_obj.indexerid)
            # noinspection PyProtectedMember
            metadata_generator._write_image(img_data, dest_path, overwrite=True)

        # If direct_call from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if not direct_call:
            with show_obj.lock:
                if anime:
                    if not show_obj.release_groups:
                        show_obj.release_groups = BlackAndWhiteList(show_obj.indexerid)

                    if whitelist:
                        shortwhitelist = short_group_names(whitelist)
                        show_obj.release_groups.set_white_keywords(shortwhitelist)
                    else:
                        show_obj.release_groups.set_white_keywords([])

                    if blacklist:
                        shortblacklist = short_group_names(blacklist)
                        show_obj.release_groups.set_black_keywords(shortblacklist)
                    else:
                        show_obj.release_groups.set_black_keywords([])

        errors = []
        with show_obj.lock:
            new_quality = Quality.combineQualities([int(q) for q in any_qualities], [int(q) for q in best_qualities])
            show_obj.quality = new_quality

            if bool(show_obj.season_folders) != season_folders:
                show_obj.season_folders = season_folders
                error, show = Show.refresh(show_obj)
                if error:
                    errors.append(_("Unable to refresh this show: {error}").format(error=error))

            show_obj.paused = paused
            show_obj.scene = scene
            show_obj.anime = anime
            show_obj.sports = sports
            show_obj.subtitles = subtitles
            show_obj.subtitles_sc_metadata = subtitles_sc_metadata
            show_obj.air_by_date = air_by_date
            show_obj.default_ep_status = default_ep_status
            # words added to mass update so moved from direct_call to here.
            show_obj.rls_ignore_words = rls_ignore_words.strip()
            show_obj.rls_require_words = rls_require_words.strip()
            show_obj.rls_prefer_words = rls_prefer_words.strip()

            if not direct_call:
                show_obj.lang = indexer_lang
                show_obj.dvdorder = dvdorder
                location = self.get_body_argument("location", show_obj.get_location)

            location = os.path.normpath(location)

            # noinspection PyProtectedMember
            old_location = os.path.normpath(show_obj.get_location)
            # if we change location clear the db of episodes, change it, write to db, and rescan
            if old_location != location:
                logger.debug(f"Changing old location {old_location} to new location {location}")
                if not (os.path.isdir(location) or settings.CREATE_MISSING_SHOW_DIRS or settings.ADD_SHOWS_WO_DIR):
                    errors.append(_("New location <tt>{location}</tt> does not exist").format(location=location))
                else:
                    # change it
                    try:
                        show_obj.location = location
                        error, show = Show.refresh(show_obj, True)
                        if error:
                            errors.append(_("Unable to refresh this show: {error}").format(error=error))
                            # grab updated info from TVDB
                            # show_obj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        errors.append(
                            f"The folder at <tt>{location}</tt> doesn't contain a tvshow.nfo - "
                            + "copy your files to that folder before you change the directory in SickChill."
                        )

            # save it to the DB
            show_obj.save_to_db()

        # force the update
        if do_update:
            error, show = Show.update(show_obj, True)
            if error:
                errors.append(_("Unable to update show: {error}").format(error=error))

            time.sleep(cpu_presets[settings.CPU_PRESET])

        logger.debug("Updating show exceptions")
        try:
            sickchill.oldbeard.scene_exceptions.update_custom_scene_exceptions(show_obj.indexerid, exceptions)
            time.sleep(cpu_presets[settings.CPU_PRESET])
        except CantUpdateShowException:
            logger.debug("Error updating scene exceptions", exc_info=True)
            errors.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                sickchill.oldbeard.scene_numbering.xem_refresh(show_obj.indexerid, show_obj.indexer)
                time.sleep(cpu_presets[settings.CPU_PRESET])
            except CantUpdateShowException:
                errors.append(_("Unable to force an update on scene numbering of the show."))

        if direct_call is True:
            return errors

        if errors:
            ui.notifications.error(
                _("{num_errors:d} error{plural} while saving changes:").format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"),
                "<ul>" + "\n".join([f"<li>{error}</li>" for error in errors]) + "</ul>",
            )

        return self.redirect("/home/displayShow?show=" + show_id)

    def togglePause(self):
        show = self.get_query_argument("show")
        error, show = Show.pause(show)
        if error:
            return self._genericMessage(_("Error"), error)

        ui.notifications.message(
            _("{show_name} has been {paused_resumed}").format(show_name=show.name, paused_resumed=(_("resumed"), _("paused"))[show.paused])
        )

        return self.redirect(f"/home/displayShow?show={show.indexerid}")

    def deleteShow(self):
        show = self.get_query_argument("show")
        full = bool(try_int(self.get_query_argument("full")))

        error, show = Show.delete(show, full)
        if error:
            return self._genericMessage(_("Error"), error)

        ui.notifications.message(
            _("{show_name} has been {deleted_trashed} {was_deleted}").format(
                show_name=show.name,
                deleted_trashed=(_("deleted"), _("trashed"))[settings.TRASH_REMOVE_SHOW],
                was_deleted=(_("(media untouched)"), _("(with all related media)"))[full],
            )
        )

        time.sleep(cpu_presets[settings.CPU_PRESET])

        # Remove show from 'RECENT SHOWS' in 'Shows' menu
        settings.SHOWS_RECENT = [x for x in settings.SHOWS_RECENT if x["indexerid"] != show.indexerid]

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect("/home/")

    def refreshShow(self):
        show = self.get_query_argument("show")
        force = bool(try_int(self.get_query_argument("force", default="0")))

        error, show = Show.refresh(show, force)

        # This is a show validation error
        if error and not show:
            return self._genericMessage(_("Error"), error)

        # This is a refresh error
        if error:
            ui.notifications.error(_("Unable to refresh this show."), error)

        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect(f"/home/displayShow?show={show.indexerid}")

    def updateShow(self):
        show = self.get_query_argument("show")
        force = bool(try_int(self.get_query_argument("force", default="0")))

        # force the update
        error, show = Show.update(show, force)

        # This is a show validation error
        if error and not show:
            return self._genericMessage(_("Error"), error)

        if error:
            ui.notifications.error(_("Unable to update this show."), f"{error}")

        # just give it some time
        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect(f"/home/displayShow?show={show.indexerid}")

    def subtitleShow(self):
        show = self.get_query_argument("show")
        show_obj = Show.find(settings.show_list, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        settings.showQueueScheduler.action.download_subtitles(show_obj)

        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect(f"/home/displayShow?show={show_obj.indexerid}")

    def updateKODI(self, show=None):
        showName = None
        show_obj = None

        if show:
            show_obj = Show.find(settings.show_list, int(show))
            if show_obj:
                showName = urllib.parse.quote_plus(show_obj.name)

        if settings.KODI_UPDATE_ONLYFIRST:
            host = settings.KODI_HOST.split(",")[0].strip()
        else:
            host = settings.KODI_HOST

        if notifiers.kodi_notifier.update_library(show_name=showName):
            ui.notifications.message(_("Library update command sent to KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))
        else:
            ui.notifications.error(_("Unable to contact one or more KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))

        if show_obj:
            return self.redirect(f"/home/displayShow?show={show_obj.indexerid}")

        return self.redirect("/home/")

    def updatePLEX(self):
        if notifiers.plex_notifier.update_library() is None:
            ui.notifications.message(_("Library update command sent to Plex Media Server host: {plex_server}").format(plex_server=settings.PLEX_SERVER_HOST))
        else:
            ui.notifications.error(_("Unable to contact Plex Media Server host: {plex_server}").format(plex_server=settings.PLEX_SERVER_HOST))
        return self.redirect("/home/")

    def updateEMBY(self, show=None):
        show_obj = None

        if show:
            show_obj = Show.find(settings.show_list, int(show))

        if notifiers.emby_notifier.update_library(show_obj):
            ui.notifications.message(_("Library update command sent to Emby host: {emby_host}").format(emby_host=settings.EMBY_HOST))
        else:
            ui.notifications.error(_("Unable to contact Emby host: {emby_host}").format(emby_host=settings.EMBY_HOST))

        if show_obj:
            return self.redirect(f"/home/displayShow?show={show_obj.indexerid}")

        return self.redirect("/home/")

    def updateJELLYFIN(self, show=None):
        show_obj = None

        if show:
            show_obj = Show.find(settings.show_list, int(show))

        if notifiers.jellyfin_notifier.update_library(show_obj):
            ui.notifications.message(_("Library update command sent to Jellyfin host: {jellyfin_host}").format(jellyfin_host=settings.JELLYFIN_HOST))
        else:
            ui.notifications.error(_("Unable to contact Jellyfin host: {jellyfin_host}").format(jellyfin_host=settings.JELLYFIN_HOST))

        if show_obj:
            return self.redirect(f"/home/displayShow?show={show_obj.indexerid}")

        return self.redirect("/home/")

    def setStatus(self, direct=False):
        if direct is True:
            # noinspection PyUnresolvedReferences
            show = self.to_change_show
            # noinspection PyUnresolvedReferences
            eps = self.to_change_eps
            status = self.get_body_argument("newStatus")
        else:
            show = self.get_body_argument("show")
            eps = self.get_body_arguments("eps[]")
            status = self.get_body_argument("status")

        if status not in statusStrings:
            errMsg = _("Invalid status")
            if direct:
                ui.notifications.error(_("Error"), errMsg)
                return json.dumps({"result": "error"})

            return self._genericMessage(_("Error"), errMsg)

        show_obj = Show.find(settings.show_list, int(show))

        if not show_obj:
            errMsg = _("Show not in show list")
            if direct:
                ui.notifications.error(_("Error"), errMsg)
                return json.dumps({"result": "error"})

            return self._genericMessage(_("Error"), errMsg)

        segments = {}
        if eps:
            trakt_data = []
            sql_l = []
            for cur_ep in eps:
                if not cur_ep:
                    logger.debug("cur_ep was empty when trying to setStatus")

                logger.debug(f"Attempting to set status of {show} episode {cur_ep} to {status}")

                # if mako changes from epStr to episode_object.episode_number see line 1600
                ep_info = cur_ep.split("x")

                if not all(ep_info):
                    logger.debug(f"Something went wrong when trying to setStatus, {episode_num(*ep_info)}")
                    continue

                episode_object = show_obj.get_episode(ep_info[0], ep_info[1])

                if not episode_object:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if episode_object.season in segments:
                        segments[episode_object.season].append(episode_object)
                    else:
                        segments[episode_object.season] = [episode_object]

                with episode_object.lock:
                    # don't let them mess up UNAIRED episodes
                    if episode_object.status == UNAIRED:
                        logger.warning(f"Refusing to change status of {cur_ep} because it is UNAIRED")
                        continue

                    if (
                        int(status) in Quality.DOWNLOADED
                        and episode_object.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [IGNORED]
                        and not os.path.isfile(episode_object.location)
                    ):
                        logger.warning(f"Refusing to change status of {cur_ep} to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if (
                        int(status) == FAILED
                        and episode_object.status
                        not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED
                    ):
                        logger.warning(f"Refusing to change status of {cur_ep} to FAILED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if episode_object.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        logger.info(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced"
                        )
                        episode_object.release_name = ""

                    episode_object.status = int(status)

                    # mass add to database
                    sql_l.append(episode_object.get_sql())

                    if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
                        trakt_data.append((episode_object.season, episode_object.episode))

            if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
                data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)
                if data["seasons"]:
                    upd = ""
                    if int(status) in [WANTED, FAILED]:
                        logger.debug(f"Add episodes, showid: indexerid {show_obj.indexerid}, Title {show_obj.name} to Watchlist")
                        upd = "add"
                    elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                        logger.debug(f"Remove episodes, showid: indexerid {show_obj.indexerid}, Title {show_obj.name} from Watchlist")
                        upd = "remove"

                    if upd:
                        notifiers.trakt_notifier.update_watchlist(show_obj, data_episode=data, update=upd)

            if sql_l:
                main_db_con = db.DBConnection()
                main_db_con.mass_action(sql_l)

        if int(status) == WANTED and not show_obj.paused:
            msg = _("Backlog was automatically started for the following seasons of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ":<br><ul>"

            for season, segment in segments.items():
                cur_backlog_queue_item = search_queue.BacklogQueueItem(show_obj, segment)
                settings.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

                msg += "<li>" + _("Season") + f" {season}</li>"
                logger.info(f"Sending backlog for {show_obj.name} season {season} because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Backlog started"), msg)
        elif int(status) == WANTED and show_obj.paused:
            logger.info(f"Some episodes were set to wanted, but {show_obj.name} is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = _(f"Retrying Search was automatically started for the following season of <b>{show_obj.name}</b>")
            msg += ":<br><ul>"

            for season, segment in segments.items():
                cur_failed_queue_item = search_queue.FailedQueueItem(show_obj, segment)
                settings.searchQueueScheduler.action.add_item(cur_failed_queue_item)

                msg += "<li>" + _("Season") + f" {season}</li>"
                logger.info(f"Retrying Search for {show_obj.name} season {season} because some eps were set to failed")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Retry Search started"), msg)

        if direct:
            return json.dumps({"result": "success"})

        return self.redirect(f"/home/displayShow?show={show}")

    def testRename(self):
        show = self.get_query_argument("show")

        show_obj = Show.find(settings.show_list, show)

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # noqa
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        show_obj.get_all_episodes(has_location=True)
        t = PageTemplate(rh=self, filename="testRename.mako")
        submenu = [{"title": _("Edit"), "path": f"home/editShow?show={show_obj.indexerid}", "icon": "ui-icon ui-icon-pencil"}]

        return t.render(
            submenu=submenu,
            show=show_obj,
            title=_("Preview Rename"),
            header=_("Preview Rename"),
            controller="home",
            action="previewRename",
        )

    def doRename(self, show=None, eps=None):
        if not (show and eps):
            return self._genericMessage(_("Error"), _("You must specify a show and at least one episode"))

        show_obj = Show.find(settings.show_list, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # noqa
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if not eps:
            return self.redirect("/home/displayShow?show=" + show)

        main_db_con = db.DBConnection()
        for cur_ep in eps.split("|"):
            ep_info = cur_ep.split("x")

            # this is probably the worst possible way to deal with double eps, but I've kinda painted myself into a corner here with this stupid database
            ep_result = main_db_con.select("SELECT location FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", [show, ep_info[0], ep_info[1]])
            if not ep_result:
                logger.warning(f"Unable to find an episode for {show}: {cur_ep} , skipping")
                continue
            related_eps_result = main_db_con.select(
                "SELECT season, episode FROM tv_episodes WHERE location = ? AND episode != ?", [ep_result[0]["location"], ep_info[1]]
            )

            root_ep_obj = show_obj.get_episode(ep_info[0], ep_info[1])
            root_ep_obj.related_episodes = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.get_episode(cur_related_ep["season"], cur_related_ep["episode"])
                if related_ep_obj not in root_ep_obj.related_episodes:
                    root_ep_obj.related_episodes.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    def manual_search_show_releases(self):
        show = self.get_query_argument("show")
        season = self.get_query_argument("season")
        episode = self.get_query_argument("episode", None)

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")

        cache_db_con = db.DBConnection("cache.db", row_type="dict")
        # show_object: TVShow = Show.find(settings.show_list, show)
        # sickchill.oldbeard.search.search_providers(
        #     show_object,
        #     show_object.get_episode(season=season, episode=episode or 1),
        #     downCurQuality=True,
        #     manual=True,
        #     manual_snatch=('season', 'episode')[episode is not None]
        # )

        if episode is not None:
            results = cache_db_con.select(
                "SELECT * FROM results WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND status != ? ORDER BY seeders DESC",
                [show, season, f"%|{episode}|%", FAILED],
            )
        else:
            show_object: TVShow = Show.find(settings.show_list, show)
            episodes_sql = "|".join([str(ep.season) for ep in show_object.get_all_episodes(season=season) if ep.season > 0])
            results = cache_db_con.select(
                "SELECT * FROM results WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND status != ? ORDER BY seeders DESC",
                [show, season, f"%{episodes_sql}%", FAILED],
            )

        for result in results:
            episodes_list = [int(ep) for ep in result["episodes"].split("|") if ep]
            if len(episodes_list) > 1:
                result["ep_string"] = f"S{result['season']:02}E{min(episodes_list)}-{max(episodes_list)}"
            else:
                result["ep_string"] = episode_num(result["season"], episodes_list[0])

        # TODO: If no cache results do a search on indexers and post back to this method.

        t = PageTemplate(rh=self, filename="manual_search_show_releases.mako")
        submenu = [{"title": _("Edit"), "path": f"home/editShow?show={show}", "icon": "fa fa-pencil"}]
        return t.render(
            submenu=submenu,
            title=_("Manual Snatch"),
            header=_("Manual Snatch"),
            controller="home",
            action="manual_search_show_releases",
            results=results,
        )

    def manual_snatch_show_release(self):
        url = self.get_body_argument("url")
        show = self.get_body_argument("show")

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        cache_db_con = db.DBConnection("cache.db", row_type="dict")
        result = cache_db_con.select_one("SELECT * FROM results WHERE url = ?", [url])
        if result:
            provider = sickchill.oldbeard.providers.getProviderClass(result.get("provider"))
            if provider.provider_type == GenericProvider.TORRENT:
                result = sickchill.oldbeard.classes.TorrentSearchResult.make_result(result)
            elif provider.provider_type == GenericProvider.NZB:
                result = sickchill.oldbeard.classes.NZBSearchResult.make_result(result)
            elif provider.provider_type == GenericProvider.NZBDATA:
                result = sickchill.oldbeard.classes.NZBDataSearchResult.make_result(result)
            else:
                result = json.dumps({"result": "failure", "message": _("Result provider not found, cannot determine type")})
        else:
            result = json.dumps({"result": "failure", "message": _("Result not found in the cache")})

        if isinstance(result, str):
            sickchill.logger.info(_("Could not snatch manually selected result: {result}").format(result=result))
        elif isinstance(result, sickchill.oldbeard.classes.SearchResult):
            sickchill.oldbeard.search.snatch_episode(result, SNATCHED_BEST)

        return self.redirect("/home/displayShow?show=" + show)

    def searchEpisode(self):
        show = self.get_query_argument("show", None)
        season = self.get_query_argument("season", None)
        episode = self.get_query_argument("episode", None)
        down_cur_quality = int(self.get_query_argument("downCurQuality", str(0)))
        # retrieve the episode object and fail if we can't get one
        episode_object, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not episode_object:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(episode_object.show, episode_object, bool(down_cur_quality))

        settings.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})  # I Actually want to call it queued, because the search hasn't been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})

        return json.dumps({"result": "failure"})

    # ## Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self):
        show = self.get_query_argument("show", None)

        def getEpisodes(search_thread, search_status):
            results = []
            show_obj = Show.find(settings.show_list, int(search_thread.show.indexerid))

            if not show_obj:
                logger.warning(f"No Show Object found for show with indexerID: {search_thread.show.indexerid}")
                return results

            # noinspection PyProtectedMember
            def relative_ep_location(ep_loc, show_loc):
                """Returns the relative location compared to the show's location"""
                if ep_loc and show_loc and ep_loc.lower().startswith(show_loc.lower()):
                    # noinspection IncorrectFormatting
                    return ep_loc[len(show_loc) + 1 :]

                return ep_loc

            if isinstance(search_thread, sickchill.oldbeard.search_queue.ManualSearchQueueItem):
                # noinspection PyProtectedMember
                results.append(
                    {
                        "show": search_thread.show.indexerid,
                        "episode": search_thread.segment.episode,
                        "episodeindexid": search_thread.segment.indexerid,
                        "season": search_thread.segment.season,
                        "searchstatus": search_status,
                        "status": statusStrings[search_thread.segment.status],
                        "quality": self.getQualityClass(search_thread.segment),
                        "overview": Overview.overviewStrings[show_obj.get_overview(search_thread.segment.status)],
                        "location": relative_ep_location(search_thread.segment.location, show_obj.get_location),
                        "size": pretty_file_size(search_thread.segment.file_size) if search_thread.segment.file_size else "",
                    }
                )
            else:
                for episode_object in search_thread.segment:
                    # noinspection PyProtectedMember
                    results.append(
                        {
                            "show": episode_object.show.indexerid,
                            "episode": episode_object.episode,
                            "episodeindexid": episode_object.indexerid,
                            "season": episode_object.season,
                            "searchstatus": search_status,
                            "status": statusStrings[episode_object.status],
                            "quality": self.getQualityClass(episode_object),
                            "overview": Overview.overviewStrings[show_obj.get_overview(episode_object.status)],
                            "location": relative_ep_location(episode_object.location, show_obj.get_location),
                            "size": pretty_file_size(episode_object.file_size) if episode_object.file_size else "",
                        }
                    )

            return results

        episodes = []

        # Queued Searches
        searchstatus = "Queued"
        for searchThread in settings.searchQueueScheduler.action.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = "Searching"
        if settings.searchQueueScheduler.action.is_manualsearch_in_progress():
            searchThread = settings.searchQueueScheduler.action.currentItem

            if searchThread.success:
                searchstatus = "Finished"

            episodes += getEpisodes(searchThread, searchstatus)

        # Finished Searches
        searchstatus = "Finished"
        for searchThread in sickchill.oldbeard.search_queue.MANUAL_SEARCH_HISTORY:
            if show and str(searchThread.show.indexerid) != show:
                continue

            if isinstance(searchThread, sickchill.oldbeard.search_queue.ManualSearchQueueItem):
                # noinspection PyTypeChecker
                if not [x for x in episodes if x["episodeindexid"] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                # ## These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segment/episodes
                # TODO: WTF is this doing? Intensive
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j["episodeindexid"]]:
                    episodes += getEpisodes(searchThread, searchstatus)

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")
        return json.dumps({"episodes": episodes})

    @staticmethod
    def getQualityClass(episode_object):
        # return the correct json value

        # Find the quality class for the episode
        ep_status_, ep_quality = Quality.splitCompositeStatus(episode_object.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self):
        show = self.get_query_argument("show", None)
        season = self.get_query_argument("season", None)
        episode = self.get_query_argument("episode", None)
        # retrieve the episode object and fail if we can't get one
        episode_object, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not episode_object:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # noinspection PyBroadException
        try:
            new_subtitles = episode_object.download_subtitles()
        except Exception:
            return json.dumps({"result": "failure"})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _("New subtitles downloaded: {new_subtitle_languages}").format(new_subtitle_languages=", ".join(new_languages))
        else:
            status = _("No subtitles downloaded")

        ui.notifications.message(episode_object.show.name, status)
        return json.dumps({"result": status, "subtitles": ",".join(episode_object.subtitles)})

    def playOnKodi(self):
        show = self.get_query_argument("show", None)
        season = self.get_query_argument("season", None)
        episode = self.get_query_argument("episode", None)
        host = self.get_query_argument("host", None)
        episode_object, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not episode_object:
            print("error")
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        sickchill.oldbeard.notifiers.kodi_notifier.play_episode(episode_object, host)
        return json.dumps({"result": "success"})

    def retrySearchSubtitles(self):
        show = self.get_query_argument("show", None)
        season = self.get_query_argument("season", None)
        episode = self.get_query_argument("episode", None)
        lang = self.get_query_argument("lang", None)
        # retrieve the episode object and fail if we can't get one
        episode_object, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not episode_object:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        try:
            new_subtitles = episode_object.download_subtitles(force_lang=lang)
        except Exception as error:
            return json.dumps({"result": "failure", "errorMessage": error})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _("New subtitles downloaded: {new_subtitle_languages}").format(new_subtitle_languages=", ".join(new_languages))
        else:
            status = _("No subtitles downloaded")

        ui.notifications.message(episode_object.show.name, status)
        return json.dumps({"result": status, "subtitles": ",".join(episode_object.subtitles)})

    def setSceneNumbering(self, show, indexer, forSeason=None, forEpisode=None, forAbsolute=None, sceneSeason=None, sceneEpisode=None, sceneAbsolute=None):
        # sanitize:
        if forSeason in ("null", ""):
            forSeason = None
        if forEpisode in ("null", ""):
            forEpisode = None
        if forAbsolute in ("null", ""):
            forAbsolute = None
        if sceneSeason in ("null", ""):
            sceneSeason = None
        if sceneEpisode in ("null", ""):
            sceneEpisode = None
        if sceneAbsolute in ("null", ""):
            sceneAbsolute = None

        show_obj = Show.find(settings.show_list, int(show))

        if show_obj.is_anime:
            result = {
                "success": True,
                "forAbsolute": forAbsolute,
            }
        else:
            result = {
                "success": True,
                "forSeason": forSeason,
                "forEpisode": forEpisode,
            }

        # retrieve the episode object and fail if we can't get one
        if show_obj.is_anime:
            episode_object, error_msg = self._getEpisode(show, absolute=forAbsolute)
        else:
            episode_object, error_msg = self._getEpisode(show, forSeason, forEpisode)

        if error_msg or not episode_object:
            result["success"] = False
            result["errorMessage"] = error_msg
        elif show_obj.is_anime:
            logger.debug(f"setAbsoluteSceneNumbering for {show} from {forAbsolute} to {sceneAbsolute}")

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            logger.debug(f"setEpisodeSceneNumbering for {show} from {episode_num(forSeason, forEpisode)} to {episode_num(sceneSeason, sceneEpisode)}")

            show = int(show)
            indexer = int(indexer)
            forSeason = int(forSeason)
            forEpisode = int(forEpisode)
            if sceneSeason is not None:
                sceneSeason = int(sceneSeason)
            if sceneEpisode is not None:
                sceneEpisode = int(sceneEpisode)

            set_scene_numbering(show, indexer, season=forSeason, episode=forEpisode, sceneSeason=sceneSeason, sceneEpisode=sceneEpisode)

        if show_obj.is_anime:
            sn = get_scene_absolute_numbering(show, indexer, forAbsolute)
            if sn:
                result["sceneAbsolute"] = sn
            else:
                result["sceneAbsolute"] = None
        else:
            sn = get_scene_numbering(show, indexer, forSeason, forEpisode)
            if sn:
                (result["sceneSeason"], result["sceneEpisode"]) = sn
            else:
                (result["sceneSeason"], result["sceneEpisode"]) = (None, None)

        return json.dumps(result)

    def retryEpisode(self):
        show = self.get_query_argument("show", None)
        season = self.get_query_argument("season", None)
        episode = self.get_query_argument("episode", None)
        down_cur_quality = int(self.get_query_argument("downCurQuality", str(0)))
        # retrieve the episode object and fail if we can't get one
        episode_object, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not episode_object:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.FailedQueueItem(episode_object.show, [episode_object], bool(down_cur_quality))
        settings.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})  # I Actually want to call it queued, because the search hasn't been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})

        return json.dumps({"result": "failure"})

    @staticmethod
    def fetch_releasegroups(show_name):
        logger.info(f"ReleaseGroups: {show_name}")
        if helpers.set_up_anidb_connection():
            try:
                anime = adba.Anime(settings.ADBA_CONNECTION, name=show_name, cache_dir=Path(settings.CACHE_DIR))
                groups = anime.get_groups()
                logger.info(f"ReleaseGroups: {groups}")
                return json.dumps({"result": "success", "groups": groups})
            except AttributeError as error:
                logger.debug(f"Unable to get ReleaseGroups: {error}", exc_info=True)

        return json.dumps({"result": "failure"})
