import ast
import base64
import datetime
import json
import os
import time
import traceback
import urllib.parse
from operator import attrgetter
from pathlib import Path
from urllib.parse import unquote_plus

import requests
from github.GithubException import GithubException
from tornado.escape import xhtml_unescape

import sickchill.oldbeard
from sickchill import adba, logger, settings
from sickchill.helper import try_int
from sickchill.helper.common import episode_num, pretty_file_size
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, NoNFOException, ShowDirectoryNotFoundException
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
from sickchill.show.Show import Show
from sickchill.system.Restart import Restart
from sickchill.system.Shutdown import Shutdown
from sickchill.tv import TVShow
from sickchill.update_manager import UpdateManager

from ..oldbeard import clients, config, db, filters, helpers, notifiers, sab, search_queue, subtitles as subtitle_module, ui
from ..providers.metadata.generic import GenericMetadata
from ..providers.metadata.helpers import getShowImage
from .common import PageTemplate
from .index import WebRoot
from .routes import Route


@Route("/home(/?.*)", name="home")
class Home(WebRoot):
    def _genericMessage(self, subject=None, message=None):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="home", title="")

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if not show:
            return None, _("Invalid show parameters")

        show_obj = Show.find(settings.showList, int(show))

        if not show_obj:
            return None, _("Invalid show parameters")

        if absolute:
            ep_obj = show_obj.getEpisode(absolute_number=absolute)
        elif season and episode:
            ep_obj = show_obj.getEpisode(season, episode)
        else:
            return None, _("Invalid parameters")

        if not ep_obj:
            return None, _("Episode couldn't be retrieved")

        return ep_obj, ""

    def index(self):
        t = PageTemplate(rh=self, filename="home.mako")

        selected_root = self.get_body_argument("root", None)
        if selected_root and settings.ROOT_DIRS:
            backend_pieces = settings.ROOT_DIRS.split("|")
            backend_dirs = backend_pieces[1:]
            try:
                assert selected_root != "-1"
                selected_root_dir = backend_dirs[int(selected_root)]
                if selected_root_dir[-1] not in ("/", "\\"):
                    selected_root_dir += os.sep
            except (IndexError, ValueError, TypeError, AssertionError):
                selected_root_dir = ""
        else:
            selected_root_dir = ""

        if settings.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in settings.showList:
                # noinspection PyProtectedMember
                if selected_root_dir in show._location:
                    if show.is_anime:
                        anime.append(show)
                    else:
                        shows.append(show)

            sortedShowLists = [
                ["Shows", sorted(shows, key=lambda mbr: attrgetter("sort_name")(mbr))],
                ["Anime", sorted(anime, key=lambda mbr: attrgetter("sort_name")(mbr))],
            ]
        else:
            shows = []
            for show in settings.showList:
                # noinspection PyProtectedMember
                if selected_root_dir in show._location:
                    shows.append(show)

            sortedShowLists = [["Shows", sorted(shows, key=lambda mbr: attrgetter("sort_name")(mbr))]]

        stats = self.show_statistics()
        return t.render(
            title=_("Home"),
            header=_("Show List"),
            topmenu="home",
            sortedShowLists=sortedShowLists,
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
        sql_statement += (" AND season > 0", "")[settings.DISPLAY_SHOW_SPECIALS] + " AND status <> " + str(UNAIRED)
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
        else:
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
    def haveTORRENT():
        host_good = (settings.TORRENT_HOST[:5] == "http:", settings.TORRENT_HOST[:5] == "https")[settings.ENABLE_HTTPS]
        if settings.USE_TORRENTS and settings.TORRENT_METHOD != "blackhole" and host_good:
            return True
        else:
            return False

    def testSABnzbd(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        username = self.get_body_argument("username")
        password = filters.unhide(settings.SAB_PASSWORD, self.get_body_argument("password"))
        apikey = filters.unhide(settings.SAB_APIKEY, self.get_body_argument("apikey"))

        host = config.clean_url(self.get_body_argument("host"))
        connection, accesMsg = sab.getSabAccesMethod(host)
        if connection:
            authed, authMsg = sab.testAuthentication(host, username, password, apikey)
            if authed:
                return _("Success. Connected and authenticated")
            else:
                return _("Authentication failed. SABnzbd expects") + " '" + accesMsg + "' " + _("as authentication method") + ", '" + authMsg + "'"
        else:
            return _("Unable to connect to host")

    @staticmethod
    def __torrent_test(host, username, password, method):
        client = clients.getClientInstance(method)
        result, message = client(host, username, password).testAuthentication()
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
        else:
            return _("Problem sending SMS: {message}".format(message=message))

    def testTelegram(self):
        telegram_id = self.get_body_argument("telegram_id")
        telegram_apikey = filters.unhide(settings.TELEGRAM_APIKEY, self.get_body_argument("telegram_apikey"))
        result, message = notifiers.telegram_notifier.test_notify(telegram_id, telegram_apikey)
        if result:
            return _("Telegram notification succeeded. Check your Telegram clients to make sure it worked")
        else:
            return _("Error sending Telegram notification: {message}".format(message=message))

    def testJoin(self):
        join_id = self.get_body_argument("join_id")
        join_apikey = filters.unhide(settings.JOIN_APIKEY, self.get_body_argument("join_apikey"))

        result, message = notifiers.join_notifier.test_notify(join_id, join_apikey)
        if result:
            return _("join notification succeeded. Check your join clients to make sure it worked")
        else:
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
        else:
            return _("Registration and Testing of growl failed {growl_host}").format(growl_host=unquote_plus(host)) + pw_append

    def testProwl(self):

        prowl_api = self.get_query_argument("prowl_api")
        prowl_priority = self.get_query_argument("prowl_priority")
        result = notifiers.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return _("Test prowl notice sent successfully")
        else:
            return _("Test prowl notice failed")

    def testBoxcar2(self):
        accesstoken = self.get_query_argument("accesstoken")
        result = notifiers.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return _("Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked")
        else:
            return _("Error sending Boxcar2 notification")

    def testPushover(self):
        userKey = self.get_query_argument("userKey")
        apiKey = self.get_query_argument("apiKey")

        result = notifiers.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return _("Pushover notification succeeded. Check your Pushover clients to make sure it worked")
        else:
            return _("Error sending Pushover notification")

    @staticmethod
    def twitterStep1():
        # noinspection PyProtectedMember
        return notifiers.twitter_notifier._get_authorization()

    def twitterStep2(self):
        key = self.get_query_argument("key")
        # noinspection PyProtectedMember
        result = notifiers.twitter_notifier._get_credentials(key)
        logger.info("result: " + str(result))
        if result:
            return _("Key verification successful")
        else:
            return _("Unable to verify key")

    @staticmethod
    def testTwitter():

        result = notifiers.twitter_notifier.test_notify()
        if result:
            return _("Tweet successful, check your twitter to make sure it worked")
        else:
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
        else:
            return _("Slack message failed")

    @staticmethod
    def testRocketChat():
        result = notifiers.rocketchat_notifier.test_notify()
        if result:
            return _("Rocket.Chat message successful")
        else:
            return _("Rocket.Chat message failed")

    @staticmethod
    def testMatrix():
        result = notifiers.matrix_notifier.test_notify()
        if result:
            return _("Matrix message successful")
        else:
            return _("Matrix message failed")

    def testDiscord(self):
        webhook = self.get_query_argument("webhook")
        name = self.get_query_argument("name")
        avatar = self.get_query_argument("avatar")
        tts = self.get_query_argument("tts")

        import validators

        if validators.url(webhook) != True:
            return _("Invalid URL for webhook")

        result = notifiers.discord_notifier.test_notify(webhook, name, avatar, tts)
        if result:
            return _("Discord message successful")
        else:
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

        finalResult = ""
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = notifiers.plex_notifier.test_notify_pht(unquote_plus(curHost), username, password)
            if len(curResult.split(":")) > 2 and "OK" in curResult.split(":")[2]:
                finalResult += _("Successful test notice sent to Plex Home Theater ... {plex_clients}").format(plex_clients=unquote_plus(curHost))
            else:
                finalResult += _("Test failed for Plex Home Theater ... {plex_clients}").format(plex_clients=unquote_plus(curHost))
            finalResult += "<br>" + "\n"

        ui.notifications.message(_("Tested Plex Home Theater(s)") + ":", unquote_plus(host.replace(",", ", ")))

        return finalResult

    def testPMS(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")

        username = self.get_query_argument("username")
        host = config.clean_hosts(self.get_query_argument("host"))
        password = filters.unhide(settings.PLEX_SERVER_PASSWORD, self.get_query_argument("password"))
        plex_server_token = self.get_query_argument("plex_server_token")

        finalResult = ""

        curResult = notifiers.plex_notifier.test_notify_pms(unquote_plus(host), username, password, plex_server_token)
        if curResult is None:
            finalResult += _("Successful test of Plex Media Server(s) ... {plex_servers}").format(plex_servers=unquote_plus(host.replace(",", ", ")))
        elif curResult is False:
            finalResult += _("Test failed, No Plex Media Server host specified")
        else:
            finalResult += _("Test failed for Plex Media Server(s) ... {plex_servers}").format(plex_servers=unquote_plus(str(curResult).replace(",", ", ")))
        finalResult += "<br>" + "\n"

        ui.notifications.message(_("Tested Plex Media Server host(s)") + ":", unquote_plus(host.replace(",", ", ")))

        return finalResult

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
        else:
            return _("Test notice failed to {emby_host}").format(emby_host=unquote_plus(host))

    def testNMJ(self):
        host = config.clean_host(self.get_body_argument("host"))
        database = self.get_body_argument("database")
        mount = self.get_body_argument("mount")

        result = notifiers.nmj_notifier.test_notify(unquote_plus(host), database, mount)
        if result:
            return _("Successfully started the scan update")
        else:
            return _("Test failed to start the scan update")

    def settingsNMJ(self):
        host = config.clean_host(self.get_body_argument("host"))
        result = notifiers.nmj_notifier.notify_settings(unquote_plus(host))
        if result:
            return '{{"message": _("Got settings from {host}"), "database": "{database}", "mount": "{mount}"}}'.format(
                **{"host": host, "database": settings.NMJ_DATABASE, "mount": settings.NMJ_MOUNT}
            )
        else:
            # noinspection PyPep8
            return '{"message": _("Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)"), "database": "", "mount": ""}'

    def testNMJv2(self):
        host = config.clean_host(self.get_body_argument("host"))
        result = notifiers.nmjv2_notifier.test_notify(unquote_plus(host))
        if result:
            return _("Test notice sent successfully to {nmj2_host}").format(nmj2_host=unquote_plus(host))
        else:
            return _("Test notice failed to {nmj2_host}").format(nmj2_host=unquote_plus(host))

    def settingsNMJv2(self):
        host = config.clean_host(self.get_body_argument("host"))
        dbloc = self.get_body_argument("dbloc")
        instance = self.get_body_argument("instance")
        result = notifiers.nmjv2_notifier.notify_settings(unquote_plus(host), dbloc, instance)
        if result:
            return '{{"message": _("NMJ Database found at: {host}"), "database": "{database}"}}'.format(**{"host": host, "database": settings.NMJv2_DATABASE})
        else:
            # noinspection PyPep8
            return (
                '{{"message": _("Unable to find NMJ Database at location: {dbloc}. Is the right location selected and PCH running?"), "database": ""}}'.format(
                    **{"dbloc": dbloc}
                )
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
        logger.debug(_(f"Checking flaresolverr uri: {uri}"))
        try:
            requests.head(uri)
            result = _("Successfully connected to flaresolverr, this is experimental!")
        except (requests.ConnectionError, requests.RequestException):
            result = _("Failed to connect to flaresolverr")

        logger.debug(_(f"Flaresolverr result: {result}"))
        return result

    @staticmethod
    def loadShowNotifyLists():

        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            notify_list = {"emails": "", "prowlAPIs": ""}
            if r["notify_list"] and len(r["notify_list"]) > 0:
                # First, handle legacy format (emails only)
                if not r["notify_list"][0] == "{":
                    notify_list["emails"] = r["notify_list"]
                else:
                    notify_list = dict(ast.literal_eval(r["notify_list"]))

            data[r["show_id"]] = {"id": r["show_id"], "name": r["show_name"], "list": notify_list["emails"], "prowl_notify_list": notify_list["prowlAPIs"]}
        data["_size"] = len(data)
        return json.dumps(data)

    def saveShowNotifyList(self):

        show = self.get_body_argument("show")
        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT show_id, notify_list FROM tv_shows WHERE show_id = ?", [show])
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
            data = {"id": r["show_id"], "email_list": notify_list["emails"], "prowl_list": notify_list["prowlAPIs"]}

        show_email = data["email_list"]
        show_prowl = data["prowl_list"]

        # Change email or prowl with new or keep the existing
        emails = self.get_body_argument("emails", show_email)
        prowlAPIs = self.get_body_argument("prowlAPIs", show_prowl)

        entries = {"emails": emails, "prowlAPIs": prowlAPIs}

        # TODO: Split emails and do validators.email
        if emails or prowlAPIs:
            result = main_db_con.action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [str(entries), show])
        else:
            result = main_db_con.action("UPDATE tv_shows SET notify_list = Null WHERE show_id = ?", [show])

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
        else:
            return _("ERROR: {last_error}").format(last_error=notifiers.email_notifier.last_err)

    def testPushalot(self):
        authorizationToken = self.get_body_argument("authorizationToken")
        result = notifiers.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return _("Pushalot notification succeeded. Check your Pushalot clients to make sure it worked")
        else:
            return _("Error sending Pushalot notification")

    def testPushbullet(self):
        api = self.get_body_argument("api")
        result = notifiers.pushbullet_notifier.test_notify(api)
        if result:
            return _("Pushbullet notification succeeded. Check your device to make sure it worked")
        else:
            return _("Error sending Pushbullet notification")

    def getPushbulletDevices(self):
        api = self.get_body_argument("api")
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

    def getPushbulletChannels(self):
        api = self.get_body_argument("api")
        result = notifiers.pushbullet_notifier.get_channels(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

    def status(self):
        tvdirFree = helpers.disk_usage_hr(settings.TV_DOWNLOAD_DIR)
        rootDir = {}

        if settings.ROOT_DIRS:
            backend_pieces = settings.ROOT_DIRS.split("|")
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if backend_dirs:
            for subject in backend_dirs:
                rootDir[subject] = helpers.disk_usage_hr(subject)

        t = PageTemplate(rh=self, filename="status.mako")
        return t.render(title=_("Status"), header=_("Status"), topmenu="system", tvdirFree=tvdirFree, rootDir=rootDir, controller="home", action="status")

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

        return t.render(title=_("Home"), header=_("Restarting SickChill"), topmenu="system", controller="home", action="restart")

    def updateCheck(self):
        pid = self.get_query_argument("pid")
        if str(pid) != str(settings.PID):
            return self.redirect("/home/")

        settings.versionCheckScheduler.action.check_for_new_version(force=True)
        settings.versionCheckScheduler.action.check_for_new_news()

        return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    def update(self, pid, branch=None):
        if str(pid) != str(settings.PID):
            return self.redirect("/home/")

        updater = UpdateManager()
        if updater.backup():
            if branch:
                settings.BRANCH = branch

            if updater.update():
                # do a hard restart
                settings.events.put(settings.events.SystemEvent.RESTART)

                t = PageTemplate(rh=self, filename="restart.mako")
                return t.render(title=_("Home"), header=_("Restarting SickChill"), topmenu="home", controller="home", action="restart")
            else:
                return self._genericMessage(_("Update Failed"), _("Update wasn't successful, not restarting. Check your log for more information."))
        else:
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    @staticmethod
    def fetchRemoteBranches():
        response = []
        try:
            gh_branches = settings.versionCheckScheduler.action.list_remote_branches()
        except GithubException:
            gh_branches = None

        if gh_branches:
            for cur_branch in gh_branches:
                branch_obj = {"name": cur_branch}
                if cur_branch == settings.BRANCH:
                    branch_obj["current"] = True

                if cur_branch == "master" or (settings.GIT_TOKEN and (settings.DEVELOPER == 1 or cur_branch == "develop")):
                    response.append(branch_obj)

        return json.dumps(response)

    def branchCheckout(self):
        branch = self.get_query_argument("branch")
        if settings.BRANCH != branch:
            settings.BRANCH = branch
            ui.notifications.message(_("Checking out branch") + ": ", branch)
            return self.redirect("/update/?pid={}&branch={}".format(settings.PID, branch))
        else:
            ui.notifications.message(_("Already on branch") + ": ", branch)
            return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    @staticmethod
    def compare_db_version():

        update_manager = UpdateManager()
        db_status = update_manager.compare_db_version()

        if db_status == "upgrade":
            logger.debug("Checkout branch has a new DB version - Upgrade")
            return json.dumps({"status": "success", "message": "upgrade"})
        elif db_status == "equal":
            logger.debug("Checkout branch has the same DB version - Equal")
            return json.dumps({"status": "success", "message": "equal"})
        elif db_status == "downgrade":
            logger.debug("Checkout branch has an old DB version - Downgrade")
            return json.dumps({"status": "success", "message": "downgrade"})
        else:
            logger.exception("Checkout branch couldn't compare DB version.")
            return json.dumps({"status": "error", "message": "General exception"})

    def displayShow(self):
        show = self.get_query_argument("show")
        # todo: add more comprehensive show validation
        try:
            show_obj = Show.find(settings.showList, int(show))
        except (ValueError, TypeError):
            return self._genericMessage(_("Error"), _("Invalid show ID: {show}").format(show=str(show)))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC", [show_obj.indexerid]
        )

        min_season = (1, 0)[settings.DISPLAY_SHOW_SPECIALS]

        sql_results = main_db_con.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season >= ? ORDER BY season DESC, episode DESC", [show_obj.indexerid, min_season]
        )

        t = PageTemplate(rh=self, filename="displayShow.mako")
        submenu = [{"title": _("Edit"), "path": "home/editShow?show={0:d}".format(show_obj.indexerid), "icon": "fa fa-pencil"}]

        try:
            showLoc = (show_obj.location, True)
        except ShowDirectoryNotFoundException:
            # noinspection PyProtectedMember
            showLoc = (show_obj._location, False)

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
                    submenu.append({"title": _("Resume"), "path": "home/togglePause?show={0:d}".format(show_obj.indexerid), "icon": "fa fa-play"})
                else:
                    submenu.append({"title": _("Pause"), "path": "home/togglePause?show={0:d}".format(show_obj.indexerid), "icon": "fa fa-pause"})

                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Remove"),
                        "path": "home/deleteShow?show={0:d}".format(show_obj.indexerid),
                        "class": "removeshow",
                        "confirm": True,
                        "icon": "fa fa-trash",
                    }
                )
                submenu.append(
                    {"title": _("Re-scan files"), "path": "home/refreshShow?show={0:d}&amp;force=1".format(show_obj.indexerid), "icon": "fa fa-refresh"}
                )
                # noinspection PyPep8
                submenu.append(
                    {"title": _("Force Full Update"), "path": "home/updateShow?show={0:d}&amp;force=1".format(show_obj.indexerid), "icon": "fa fa-exchange"}
                )
                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Update show in KODI"),
                        "path": "home/updateKODI?show={0:d}".format(show_obj.indexerid),
                        "requires": self.haveKODI(),
                        "icon": "menu-icon-kodi",
                    }
                )
                # noinspection PyPep8
                submenu.append(
                    {
                        "title": _("Update show in Emby"),
                        "path": "home/updateEMBY?show={0:d}".format(show_obj.indexerid),
                        "requires": self.haveEMBY(),
                        "icon": "menu-icon-emby",
                    }
                )
                if seasonResults and int(seasonResults[-1]["season"]) == 0:
                    if settings.DISPLAY_SHOW_SPECIALS:
                        # noinspection PyPep8
                        submenu.append(
                            {
                                "title": _("Hide specials"),
                                "path": "home/toggleDisplayShowSpecials/?show={0:d}".format(show_obj.indexerid),
                                "confirm": True,
                                "icon": "fa fa-times",
                            }
                        )
                    else:
                        # noinspection PyPep8
                        submenu.append(
                            {
                                "title": _("Show specials"),
                                "path": "home/toggleDisplayShowSpecials/?show={0:d}".format(show_obj.indexerid),
                                "confirm": True,
                                "icon": "fa fa-check",
                            }
                        )

                submenu.append({"title": _("Preview Rename"), "path": "home/testRename?show={0:d}".format(show_obj.indexerid), "icon": "fa fa-tag"})

                if settings.USE_SUBTITLES and show_obj.subtitles and not settings.showQueueScheduler.action.is_being_subtitled(show_obj):
                    # noinspection PyPep8
                    submenu.append(
                        {"title": _("Download Subtitles"), "path": "home/subtitleShow?show={0:d}".format(show_obj.indexerid), "icon": "fa fa-language"}
                    )

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

        for curResult in sql_results:
            curEpCat = show_obj.getOverview(curResult["status"])
            if curEpCat:
                epCats[str(curResult["season"]) + "x" + str(curResult["episode"])] = curEpCat
                epCounts[curEpCat] += 1

        if settings.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in settings.showList:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            sortedShowLists = [
                ["Shows", sorted(shows, key=lambda mbr: attrgetter("sort_name")(mbr))],
                ["Anime", sorted(anime, key=lambda mbr: attrgetter("sort_name")(mbr))],
            ]
        else:
            sortedShowLists = [["Shows", sorted(settings.showList, key=lambda mbr: attrgetter("sort_name")(mbr))]]

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
            showLoc=showLoc,
            show_message=show_message,
            show=show_obj,
            sql_results=sql_results,
            seasonResults=seasonResults,
            sortedShowLists=sortedShowLists,
            bwl=bwl,
            epCounts=epCounts,
            epCats=epCats,
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
        show = self.get_query_argument("show")
        exeptions_list = sickchill.oldbeard.scene_exceptions.get_all_scene_exceptions(show)
        if not exeptions_list:
            return _("No scene exceptions")

        out = []
        for season, exceptions in iter(sorted(exeptions_list.items())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(exceptions.names))
        return "<br>".join(out)

    def editShow(
        self,
        show=None,
        location=None,
        anyQualities=None,
        bestQualities=None,
        exceptions_list=None,
        season_folders=None,
        paused=None,
        directCall=False,
        air_by_date=None,
        sports=None,
        dvdorder=None,
        indexerLang=None,
        subtitles=None,
        subtitles_sr_metadata=None,
        rls_ignore_words=None,
        rls_require_words=None,
        rls_prefer_words=None,
        anime=None,
        blacklist=None,
        whitelist=None,
        scene=None,
        defaultEpStatus=None,
        quality_preset=None,
        custom_name="",
        poster=None,
        banner=None,
        fanart=None,
    ):

        anidb_failed = False

        try:
            show_obj = Show.find(settings.showList, int(show))
        except (ValueError, TypeError):
            errString = _("Invalid show ID") + ": {show}".format(show=str(show))
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        if not show_obj:
            errString = _("Unable to find the specified show") + ": {show}".format(show=str(show))
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        show_obj.exceptions = sickchill.oldbeard.scene_exceptions.get_all_scene_exceptions(show_obj.indexerid)

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC", [show_obj.indexerid]
        )

        if try_int(quality_preset, None):
            bestQualities = []

        if not (location or anyQualities or bestQualities or season_folders):
            t = PageTemplate(rh=self, filename="editShow.mako")
            groups = []

            if show_obj.is_anime:
                whitelist = show_obj.release_groups.whitelist
                blacklist = show_obj.release_groups.blacklist

                if helpers.set_up_anidb_connection() and not anidb_failed:
                    try:
                        anime = adba.Anime(settings.ADBA_CONNECTION, name=show_obj.name, cache_dir=Path(settings.CACHE_DIR))
                        groups = anime.get_groups()
                    except Exception as e:
                        ui.notifications.error(_("Unable to retreive Fansub Groups from AniDB."))
                        logger.debug("Unable to retreive Fansub Groups from AniDB. Error is {0}".format(e))

            with show_obj.lock:
                show = show_obj

            if show_obj.is_anime:
                return t.render(
                    show=show,
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
            else:
                return t.render(
                    show=show,
                    scene_exceptions=show_obj.exceptions,
                    seasonResults=seasonResults,
                    title=_("Edit Show"),
                    header=_("Edit Show"),
                    controller="home",
                    action="editShow",
                )

        season_folders = config.checkbox_to_value(season_folders)
        dvdorder = config.checkbox_to_value(dvdorder)
        paused = config.checkbox_to_value(paused)
        air_by_date = config.checkbox_to_value(air_by_date)
        scene = config.checkbox_to_value(scene)
        sports = config.checkbox_to_value(sports)
        anime = config.checkbox_to_value(anime)
        subtitles = config.checkbox_to_value(subtitles)
        subtitles_sr_metadata = config.checkbox_to_value(subtitles_sr_metadata)

        if indexerLang and indexerLang in show_obj.idxr.languages:
            indexer_lang = indexerLang
        else:
            indexer_lang = show_obj.lang

        # if we changed the language then kick off an update
        do_update = indexer_lang != show_obj.lang
        do_update_scene_numbering = scene != show_obj.scene or anime != show_obj.anime

        if not anyQualities:
            anyQualities = []

        if not bestQualities:
            bestQualities = []

        if not exceptions_list:
            exceptions_list = []

        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]

        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]

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
                img_data = base64.b64decode(image[start:])
                return img_data, img_data
            else:
                image_parts = image.split("|")
                img_url = image_parts[0]
                img_data = getShowImage(img_url)
                if len(image_parts) > 1:
                    img_thumb_url = image_parts[1]
                    img_thumb_data = getShowImage(img_thumb_url)
                    return img_data, img_thumb_data
                else:
                    return img_data, img_data

        if poster:
            img_data, img_thumb_data = get_images(poster)
            dest_path = settings.IMAGE_CACHE.poster_path(show_obj.indexerid)
            dest_thumb_path = settings.IMAGE_CACHE.poster_thumb_path(show_obj.indexerid)
            metadata_generator._write_image(img_data, dest_path, overwrite=True)
            metadata_generator._write_image(img_thumb_data, dest_thumb_path, overwrite=True)
        if banner:
            img_data, img_thumb_data = get_images(banner)
            dest_path = settings.IMAGE_CACHE.banner_path(show_obj.indexerid)
            dest_thumb_path = settings.IMAGE_CACHE.banner_thumb_path(show_obj.indexerid)
            metadata_generator._write_image(img_data, dest_path, overwrite=True)
            metadata_generator._write_image(img_thumb_data, dest_thumb_path, overwrite=True)
        if fanart:
            img_data, img_thumb_data = get_images(fanart)
            dest_path = settings.IMAGE_CACHE.fanart_path(show_obj.indexerid)
            metadata_generator._write_image(img_data, dest_path, overwrite=True)

        # If directCall from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if not directCall:
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
            newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])
            show_obj.quality = newQuality

            if bool(show_obj.season_folders) != season_folders:
                show_obj.season_folders = season_folders
                try:
                    settings.showQueueScheduler.action.refresh_show(show_obj)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh this show: {error}").format(error=e))

            show_obj.paused = paused
            show_obj.scene = scene
            show_obj.anime = anime
            show_obj.sports = sports
            show_obj.subtitles = subtitles
            show_obj.subtitles_sr_metadata = subtitles_sr_metadata
            show_obj.air_by_date = air_by_date
            show_obj.default_ep_status = int(defaultEpStatus)

            if not directCall:
                show_obj.lang = indexer_lang
                show_obj.dvdorder = dvdorder
                show_obj.rls_ignore_words = rls_ignore_words.strip()
                show_obj.rls_require_words = rls_require_words.strip()
                show_obj.rls_prefer_words = rls_prefer_words.strip()

            location = os.path.normpath(xhtml_unescape(location))
            # noinspection PyProtectedMember
            old_location = os.path.normpath(show_obj._location)
            # if we change location clear the db of episodes, change it, write to db, and rescan
            if old_location != location:
                logger.debug(old_location + " != " + location)
                if not (os.path.isdir(location) or settings.CREATE_MISSING_SHOW_DIRS or settings.ADD_SHOWS_WO_DIR):
                    errors.append(_("New location <tt>{location}</tt> does not exist").format(location=location))
                else:
                    # change it
                    try:
                        show_obj.location = location
                        try:
                            settings.showQueueScheduler.action.refresh_show(show_obj, True)
                        except CantRefreshShowException as e:
                            errors.append(_("Unable to refresh this show: {error}").format(error=e))
                            # grab updated info from TVDB
                            # show_obj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        # noinspection PyPep8
                        errors.append(
                            "The folder at <tt>{0}</tt> doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SickChill.".format(
                                location
                            )
                        )

            # save it to the DB
            show_obj.saveToDB()

        # force the update
        if do_update:
            try:
                settings.showQueueScheduler.action.update_show(show_obj, True)
                time.sleep(cpu_presets[settings.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {error}").format(error=e))

        import traceback

        logger.debug("Updating show exceptions")
        try:
            sickchill.oldbeard.scene_exceptions.update_custom_scene_exceptions(show_obj.indexerid, exceptions)
            time.sleep(cpu_presets[settings.CPU_PRESET])
        except CantUpdateShowException:
            logger.debug(traceback.format_exc())
            errors.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                sickchill.oldbeard.scene_numbering.xem_refresh(show_obj.indexerid, show_obj.indexer)
                time.sleep(cpu_presets[settings.CPU_PRESET])
            except CantUpdateShowException:
                errors.append(_("Unable to force an update on scene numbering of the show."))

        if directCall:
            return errors

        if errors:
            ui.notifications.error(
                _("{num_errors:d} error{plural} while saving changes:").format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"),
                "<ul>" + "\n".join(["<li>{0}</li>".format(error) for error in errors]) + "</ul>",
            )

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = Show.pause(show)

        if error:
            return self._genericMessage(_("Error"), error)

        ui.notifications.message(
            _("{show_name} has been {paused_resumed}").format(show_name=show.name, paused_resumed=(_("resumed"), _("paused"))[show.paused])
        )

        return self.redirect("/home/displayShow?show={0:d}".format(show.indexerid))

    def deleteShow(self, show=None, full=0):
        if show:
            error, show = Show.delete(show, full)

            if error:
                return self._genericMessage(_("Error"), error)

            ui.notifications.message(
                _("{show_name} has been {deleted_trashed} {was_deleted}").format(
                    show_name=show.name,
                    deleted_trashed=(_("deleted"), _("trashed"))[settings.TRASH_REMOVE_SHOW],
                    was_deleted=(_("(media untouched)"), _("(with all related media)"))[bool(full)],
                )
            )

            time.sleep(cpu_presets[settings.CPU_PRESET])

        # Remove show from 'RECENT SHOWS' in 'Shows' menu
        settings.SHOWS_RECENT = [x for x in settings.SHOWS_RECENT if x["indexerid"] != show.indexerid]

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect("/home/")

    def refreshShow(self, show=None, force=False):
        error, show = Show.refresh(show, force)

        # This is a show validation error
        if error and not show:
            return self._genericMessage(_("Error"), error)

        # This is a refresh error
        if error:
            ui.notifications.error(_("Unable to refresh this show."), error)

        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show.indexerid))

    def updateShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(settings.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            settings.showQueueScheduler.action.update_show(show_obj, bool(force))
        except CantUpdateShowException as e:
            ui.notifications.error(_("Unable to update this show."), str(e))

        # just give it some time
        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(settings.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        settings.showQueueScheduler.action.download_subtitles(show_obj, bool(force))

        time.sleep(cpu_presets[settings.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        show_obj = None

        if show:
            show_obj = Show.find(settings.showList, int(show))
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
            return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))
        else:
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
            show_obj = Show.find(settings.showList, int(show))

        if notifiers.emby_notifier.update_library(show_obj):
            ui.notifications.message(_("Library update command sent to Emby host: {emby_host}").format(emby_host=settings.EMBY_HOST))
        else:
            ui.notifications.error(_("Unable to contact Emby host: {emby_host}").format(emby_host=settings.EMBY_HOST))

        if show_obj:
            return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))
        else:
            return self.redirect("/home/")

    def setStatus(self, show=None, eps=None, status=None, direct=False):

        if not all([show, eps, status]):
            errMsg = _("You must specify a show and at least one episode")
            if direct:
                ui.notifications.error(_("Error"), errMsg)
                return json.dumps({"result": "error"})
            else:
                return self._genericMessage(_("Error"), errMsg)

        # Use .has_key() since it is overridden for statusStrings in common.py
        if status not in statusStrings:
            errMsg = _("Invalid status")
            if direct:
                ui.notifications.error(_("Error"), errMsg)
                return json.dumps({"result": "error"})
            else:
                return self._genericMessage(_("Error"), errMsg)

        show_obj = Show.find(settings.showList, int(show))

        if not show_obj:
            errMsg = _("Show not in show list")
            if direct:
                ui.notifications.error(_("Error"), errMsg)
                return json.dumps({"result": "error"})
            else:
                return self._genericMessage(_("Error"), errMsg)

        segments = {}
        if eps:
            trakt_data = []
            sql_l = []
            for cur_ep in eps.split("|"):

                if not cur_ep:
                    logger.debug("cur_ep was empty when trying to setStatus")

                logger.debug("Attempting to set status on episode " + cur_ep + " to " + status)

                epInfo = cur_ep.split("x")

                if not all(epInfo):
                    logger.debug("Something went wrong when trying to setStatus, epInfo[0]: {0}, epInfo[1]: {1}".format(epInfo[0], epInfo[1]))
                    continue

                ep_obj = show_obj.getEpisode(epInfo[0], epInfo[1])

                if not ep_obj:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if ep_obj.season in segments:
                        segments[ep_obj.season].append(ep_obj)
                    else:
                        segments[ep_obj.season] = [ep_obj]

                with ep_obj.lock:
                    # don't let them mess up UNAIRED episodes
                    if ep_obj.status == UNAIRED:
                        logger.warning("Refusing to change status of " + cur_ep + " because it is UNAIRED")
                        continue

                    if (
                        int(status) in Quality.DOWNLOADED
                        and ep_obj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [IGNORED]
                        and not os.path.isfile(ep_obj.location)
                    ):
                        logger.warning("Refusing to change status of " + cur_ep + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if (
                        int(status) == FAILED
                        and ep_obj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED
                    ):
                        logger.warning("Refusing to change status of " + cur_ep + " to FAILED because it's not SNATCHED/DOWNLOADED")
                        continue

                    if ep_obj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        logger.info(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced"
                        )
                        ep_obj.release_name = ""

                    ep_obj.status = int(status)

                    # mass add to database
                    sql_l.append(ep_obj.get_sql())

                    if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
                        trakt_data.append((ep_obj.season, ep_obj.episode))

            if settings.USE_TRAKT and settings.TRAKT_SYNC_WATCHLIST:
                data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)
                if data["seasons"]:
                    upd = ""
                    if int(status) in [WANTED, FAILED]:
                        logger.debug("Add episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " to Watchlist")
                        upd = "add"
                    elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                        # noinspection PyPep8
                        logger.debug("Remove episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " from Watchlist")
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

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.info("Sending backlog for " + show_obj.name + " season " + str(season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Backlog started"), msg)
        elif int(status) == WANTED and show_obj.paused:
            logger.info("Some episodes were set to wanted, but " + show_obj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = _("Retrying Search was automatically started for the following season of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ":<br><ul>"

            for season, segment in segments.items():
                cur_failed_queue_item = search_queue.FailedQueueItem(show_obj, segment)
                settings.searchQueueScheduler.action.add_item(cur_failed_queue_item)

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.info("Retrying Search for " + show_obj.name + " season " + str(season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Retry Search started"), msg)

        if direct:
            return json.dumps({"result": "success"})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def testRename(self, show=None):

        if not show:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        show_obj = Show.find(settings.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        show_obj.getAllEpisodes(has_location=True)
        t = PageTemplate(rh=self, filename="testRename.mako")
        submenu = [{"title": _("Edit"), "path": "home/editShow?show={0:d}".format(show_obj.indexerid), "icon": "ui-icon ui-icon-pencil"}]

        return t.render(submenu=submenu, show=show_obj, title=_("Preview Rename"), header=_("Preview Rename"), controller="home", action="previewRename")

    def doRename(self, show=None, eps=None):
        if not (show and eps):
            return self._genericMessage(_("Error"), _("You must specify a show and at least one episode"))

        show_obj = Show.find(settings.showList, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if not eps:
            return self.redirect("/home/displayShow?show=" + show)

        main_db_con = db.DBConnection()
        for cur_ep in eps.split("|"):

            epInfo = cur_ep.split("x")

            # this is probably the worst possible way to deal with double eps but I've kinda painted myself into a corner here with this stupid database
            ep_result = main_db_con.select(
                "SELECT location FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND 5=5", [show, epInfo[0], epInfo[1]]
            )
            if not ep_result:
                logger.warning("Unable to find an episode for " + cur_ep + ", skipping")
                continue
            related_eps_result = main_db_con.select(
                "SELECT season, episode FROM tv_episodes WHERE location = ? AND episode != ?", [ep_result[0]["location"], epInfo[1]]
            )

            root_ep_obj = show_obj.getEpisode(epInfo[0], epInfo[1])
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(cur_related_ep["season"], cur_related_ep["episode"])
                if related_ep_obj not in root_ep_obj.relatedEps:
                    root_ep_obj.relatedEps.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    def manual_search_show_releases(self):
        show = self.get_query_argument("show")
        season = self.get_query_argument("season")
        episode = self.get_query_argument("episode", None)

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")

        cache_db_con = db.DBConnection("cache.db", row_type="dict")
        # show_object: TVShow = Show.find(settings.showList, show)
        # sickchill.oldbeard.search.searchProviders(
        #     show_object,
        #     show_object.getEpisode(season=season, episode=episode or 1),
        #     downCurQuality=True,
        #     manualSearch=True,
        #     manual_snatch=('sponly', 'eponly')[episode is not None]
        # )

        if episode:
            results = cache_db_con.select(
                "SELECT * FROM results WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND status != ? ORDER BY seeders DESC",
                [show, season, f"%|{episode}|%", FAILED],
            )
        else:
            show_object: TVShow = Show.find(settings.showList, show)
            episodes_sql = "|".join([str(ep.season) for ep in show_object.getAllEpisodes(season=season) if ep.season > 0])
            results = cache_db_con.select(
                "SELECT * FROM results WHERE indexerid = ? AND season = ? AND episodes LIKE ? AND status != ? ORDER BY seeders DESC",
                [show, season, f"%{episodes_sql}%", FAILED],
            )

        for result in results:
            episodes_list = [int(ep) for ep in result["episodes"].split("|") if ep]
            if len(episodes_list) > 1:
                result["ep_string"] = "S{:02}E{}-{}".format(result["season"], min(episodes_list), max(episodes_list))
            else:
                result["ep_string"] = episode_num(result["season"], episodes_list[0])

        # TODO: If no cache results do a search on indexers and post back to this method.

        t = PageTemplate(rh=self, filename="manual_search_show_releases.mako")
        submenu = [{"title": _("Edit"), "path": "home/editShow?show={0}".format(show), "icon": "fa fa-pencil"}]
        return t.render(
            submenu=submenu, title=_("Manual Snatch"), header=_("Manual Snatch"), controller="home", action="manual_search_show_releases", results=results
        )

    def manual_snatch_show_release(self, *args, **kwargs):
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
            sickchill.logger.info(_(f"Could not snatch manually selected result: {result}"))
        elif isinstance(result, sickchill.oldbeard.classes.SearchResult):
            sickchill.oldbeard.search.snatchEpisode(result, SNATCHED_BEST)

        return self.redirect("/home/displayShow?show=" + show)

    def searchEpisode(self, show=None, season=None, episode=None, downCurQuality=0):

        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(ep_obj.show, ep_obj, bool(int(downCurQuality)))

        settings.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})
        else:
            return json.dumps({"result": "failure"})

    # ## Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(search_thread, search_status):
            results = []
            show_obj = Show.find(settings.showList, int(search_thread.show.indexerid))

            if not show_obj:
                logger.warning("No Show Object found for show with indexerID: " + str(search_thread.show.indexerid))
                return results

            # noinspection PyProtectedMember
            def relative_ep_location(ep_loc, show_loc):
                """Returns the relative location compared to the show's location"""
                if ep_loc and show_loc and ep_loc.lower().startswith(show_loc.lower()):
                    return ep_loc[len(show_loc) + 1 :]
                else:
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
                        "overview": Overview.overviewStrings[show_obj.getOverview(search_thread.segment.status)],
                        "location": relative_ep_location(search_thread.segment._location, show_obj._location),
                        "size": pretty_file_size(search_thread.segment.file_size) if search_thread.segment.file_size else "",
                    }
                )
            else:
                for ep_obj in search_thread.segment:
                    # noinspection PyProtectedMember
                    results.append(
                        {
                            "show": ep_obj.show.indexerid,
                            "episode": ep_obj.episode,
                            "episodeindexid": ep_obj.indexerid,
                            "season": ep_obj.season,
                            "searchstatus": search_status,
                            "status": statusStrings[ep_obj.status],
                            "quality": self.getQualityClass(ep_obj),
                            "overview": Overview.overviewStrings[show_obj.getOverview(ep_obj.status)],
                            "location": relative_ep_location(ep_obj._location, show_obj._location),
                            "size": pretty_file_size(ep_obj.file_size) if ep_obj.file_size else "",
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
    def getQualityClass(ep_obj):
        # return the correct json value

        # Find the quality class for the episode
        ep_status_, ep_quality = Quality.splitCompositeStatus(ep_obj.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self, show=None, season=None, episode=None):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # noinspection PyBroadException
        try:
            new_subtitles = ep_obj.download_subtitles()
        except Exception:
            return json.dumps({"result": "failure"})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _("New subtitles downloaded: {new_subtitle_languages}").format(new_subtitle_languages=", ".join(new_languages))
        else:
            status = _("No subtitles downloaded")

        ui.notifications.message(ep_obj.show.name, status)
        return json.dumps({"result": status, "subtitles": ",".join(ep_obj.subtitles)})

    def playOnKodi(self, show, season, episode, host):
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            print("error")
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        sickchill.oldbeard.notifiers.kodi_notifier.play_episode(ep_obj, host)
        return json.dumps({"result": "success"})

    def retrySearchSubtitles(self, show, season, episode, lang):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        try:
            new_subtitles = ep_obj.download_subtitles(force_lang=lang)
        except Exception as error:
            return json.dumps({"result": "failure", "errorMessage": error})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _("New subtitles downloaded: {new_subtitle_languages}").format(new_subtitle_languages=", ".join(new_languages))
        else:
            status = _("No subtitles downloaded")

        ui.notifications.message(ep_obj.show.name, status)
        return json.dumps({"result": status, "subtitles": ",".join(ep_obj.subtitles)})

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

        show_obj = Show.find(settings.showList, int(show))

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
            ep_obj, error_msg = self._getEpisode(show, absolute=forAbsolute)
        else:
            ep_obj, error_msg = self._getEpisode(show, forSeason, forEpisode)

        if error_msg or not ep_obj:
            result["success"] = False
            result["errorMessage"] = error_msg
        elif show_obj.is_anime:
            logger.debug("setAbsoluteSceneNumbering for {0} from {1} to {2}".format(show, forAbsolute, sceneAbsolute))

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            logger.debug("setEpisodeSceneNumbering for {0} from {1}x{2} to {3}x{4}".format(show, forSeason, forEpisode, sceneSeason, sceneEpisode))

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

    def retryEpisode(self, show, season, episode, downCurQuality=0):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({"result": "failure", "errorMessage": error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.FailedQueueItem(ep_obj.show, [ep_obj], bool(int(downCurQuality)))
        settings.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({"result": "success"})
        else:
            return json.dumps({"result": "failure"})

    @staticmethod
    def fetch_releasegroups(show_name):
        logger.info("ReleaseGroups: {0}".format(show_name))
        if helpers.set_up_anidb_connection():
            try:
                anime = adba.Anime(settings.ADBA_CONNECTION, name=show_name, cache_dir=Path(settings.CACHE_DIR))
                groups = anime.get_groups()
                logger.info("ReleaseGroups: {0}".format(groups))
                return json.dumps({"result": "success", "groups": groups})
            except AttributeError as error:
                logger.debug("Unable to get ReleaseGroups: {0}".format(error))
                logger.debug(traceback.format_exc())

        return json.dumps({"result": "failure"})
