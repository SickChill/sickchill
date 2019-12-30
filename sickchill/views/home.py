# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=abstract-method,too-many-lines, R

from __future__ import absolute_import, print_function, unicode_literals

import ast
import datetime
import os
import time
from operator import attrgetter

import adba
import six
from github.GithubException import GithubException
from libtrakt import TraktAPI
from requests.compat import unquote_plus
from six.moves import urllib
from tornado.escape import xhtml_unescape

import sickbeard
from sickbeard import clients, config, db, filters, helpers, logger, notifiers, sab, search_queue, subtitles as subtitle_module, ui
from sickbeard.blackandwhitelist import BlackAndWhiteList, short_group_names
from sickbeard.common import cpu_presets, FAILED, IGNORED, Overview, Quality, SKIPPED, statusStrings, UNAIRED, WANTED
from sickbeard.scene_numbering import (get_scene_absolute_numbering, get_scene_absolute_numbering_for_show, get_scene_numbering, get_scene_numbering_for_show,
                                       get_xem_absolute_numbering_for_show, get_xem_numbering_for_show, set_scene_numbering)
from sickbeard.versionChecker import CheckVersion
from sickchill.helper import try_int
from sickchill.helper.common import pretty_file_size
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex, NoNFOException, ShowDirectoryNotFoundException
from sickchill.show.Show import Show
from sickchill.system.Restart import Restart
from sickchill.system.Shutdown import Shutdown

from .common import PageTemplate
from .index import WebRoot
from .routes import Route

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/home(/?.*)', name='home')
class Home(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    def _genericMessage(self, subject, message):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="home", title="")

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if not show:
            return None, _("Invalid show parameters")

        show_obj = Show.find(sickbeard.showList, int(show))

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

        return ep_obj, ''

    def index(self, *args, **kwargs):
        t = PageTemplate(rh=self, filename="home.mako")

        selected_root = kwargs.get('root')
        if selected_root and sickbeard.ROOT_DIRS:
            backend_pieces = sickbeard.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
            try:
                assert selected_root != '-1'
                selected_root_dir = backend_dirs[int(selected_root)]
                if selected_root_dir[-1] not in ('/', '\\'):
                    selected_root_dir += os.sep
            except (IndexError, ValueError, TypeError, AssertionError):
                selected_root_dir = ''
        else:
            selected_root_dir = ''

        if sickbeard.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickbeard.showList:
                # noinspection PyProtectedMember
                if selected_root_dir in show._location:
                    if show.is_anime:
                        anime.append(show)
                    else:
                        shows.append(show)

            sortedShowLists = [
                ["Shows", sorted(shows, key=lambda mbr: attrgetter('sort_name')(mbr))],
                ["Anime", sorted(anime, key=lambda mbr: attrgetter('sort_name')(mbr))]
            ]
        else:
            shows = []
            for show in sickbeard.showList:
                # noinspection PyProtectedMember
                if selected_root_dir in show._location:
                    shows.append(show)

            sortedShowLists = [
                ["Shows", sorted(shows, key=lambda mbr: attrgetter('sort_name')(mbr))]
            ]

        stats = self.show_statistics()
        return t.render(title=_("Home"), header=_("Show List"), topmenu="home", sortedShowLists=sortedShowLists, show_stat=stats[
            0], max_download_count=stats[1], controller="home", action="index", selected_root=selected_root or '-1')

    @staticmethod
    def show_statistics():
        """ Loads show and episode statistics from db """
        main_db_con = db.DBConnection()
        today = str(datetime.date.today().toordinal())

        status_quality = '(' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST]) + ')'
        status_download = '(' + ','.join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ')'

        sql_statement = 'SELECT showid,'

        # noinspection PyPep8
        sql_statement += ' (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_quality + ') AS ep_snatched,'
        # noinspection PyPep8
        sql_statement += ' (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_download + ') AS ep_downloaded,'
        sql_statement += ' (SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1'
        sql_statement += ' AND ((airdate <= ' + today + ' AND status IN (' + ','.join([str(SKIPPED), str(WANTED), str(FAILED)]) + '))'
        sql_statement += ' OR (status IN ' + status_quality + ') OR (status IN ' + status_download + '))) AS ep_total,'

        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= ' + today
        sql_statement += (' AND season > 0', '')[sickbeard.DISPLAY_SHOW_SPECIALS] + ' AND status IN (' + ','.join([str(UNAIRED), str(WANTED)]) + ')'
        sql_statement += ' ORDER BY airdate ASC LIMIT 1) AS ep_airs_next,'

        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1'
        sql_statement += (' AND season > 0', '')[sickbeard.DISPLAY_SHOW_SPECIALS] + ' AND status <> ' + str(UNAIRED)
        sql_statement += ' ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev,'

        # @TODO: Store each show_size in tv_shows. also change in displayShow.mako:250, where we use helpers.get_size()
        sql_statement += ' (SELECT SUM(file_size) FROM tv_episodes WHERE showid=tv_eps.showid) AS show_size'
        sql_statement += ' FROM tv_episodes tv_eps GROUP BY showid'

        sql_result = main_db_con.select(sql_statement)

        show_stat = {}
        max_download_count = 1000
        for cur_result in sql_result:
            show_stat[cur_result[b'showid']] = cur_result
            if cur_result[b'ep_total'] > max_download_count:
                max_download_count = cur_result[b'ep_total']

        max_download_count *= 100

        return show_stat, max_download_count

    def is_alive(self, *args_, **kwargs):
        callback, jq_obj = kwargs.get('callback'), kwargs.get('_')
        if not callback and jq_obj:
            return _("Error: Unsupported Request. Send jsonp request with 'callback' variable in the query string.")

        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header(b'Content-Type', 'text/javascript')
        self.set_header(b'Access-Control-Allow-Origin', '*')
        self.set_header(b'Access-Control-Allow-Headers', 'x-requested-with')

        if sickbeard.started:
            return (callback or '') + '(' + json.dumps(
                {"msg": str(sickbeard.PID)}) + ');'
        else:
            return (callback or '') + '(' + json.dumps({"msg": "nope"}) + ');'

    @staticmethod
    def haveKODI():
        return sickbeard.USE_KODI and sickbeard.KODI_UPDATE_LIBRARY

    @staticmethod
    def havePLEX():
        return sickbeard.USE_PLEX_SERVER and sickbeard.PLEX_UPDATE_LIBRARY

    @staticmethod
    def haveEMBY():
        return sickbeard.USE_EMBY

    @staticmethod
    def haveTORRENT():
        if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and \
            (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not
            sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
            return True
        else:
            return False

    @staticmethod
    def testSABnzbd(host=None, username=None, password=None, apikey=None):
        # self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_url(host)
        connection, accesMsg = sab.getSabAccesMethod(host)
        if connection:
            password = filters.unhide(sickbeard.SAB_PASSWORD, password)
            apikey = filters.unhide(sickbeard.SAB_APIKEY, apikey)
            authed, authMsg = sab.testAuthentication(host, username, password, apikey)  # @UnusedVariable
            if authed:
                return _("Success. Connected and authenticated")
            else:
                return _("Authentication failed. SABnzbd expects") + " '" + accesMsg + "' " + _("as authentication method") + ", '" + authMsg + "'"
        else:
            return _("Unable to connect to host")

    def testDSM(self, host=None, username=None, password=None):
        password = filters.unhide(sickbeard.SYNOLOGY_DSM_PASSWORD, password)
        return self.testTorrent('download_station', host, username, password)

    @staticmethod
    def testTorrent(torrent_method=None, host=None, username=None, password=None):
        host = config.clean_url(host)
        client = clients.getClientInstance(torrent_method)
        password = filters.unhide(sickbeard.TORRENT_PASSWORD, password)
        result_, accesMsg = client(host, username, password).testAuthentication()

        return accesMsg

    @staticmethod
    def testFreeMobile(freemobile_id=None, freemobile_apikey=None):
        freemobile_apikey = filters.unhide(sickbeard.FREEMOBILE_APIKEY, freemobile_apikey)
        result, message = notifiers.freemobile_notifier.test_notify(freemobile_id, freemobile_apikey)
        if result:
            return _("SMS sent successfully")
        else:
            return _("Problem sending SMS: {message}").format(message=message)

    @staticmethod
    def testTelegram(telegram_id=None, telegram_apikey=None):
        telegram_apikey = filters.unhide(sickbeard.TELEGRAM_APIKEY, telegram_apikey)
        result, message = notifiers.telegram_notifier.test_notify(telegram_id, telegram_apikey)
        if result:
            return _("Telegram notification succeeded. Check your Telegram clients to make sure it worked")
        else:
            return _("Error sending Telegram notification: {message}").format(message=message)

    @staticmethod
    def testJoin(join_id=None, join_apikey=None):
        join_apikey = filters.unhide(sickbeard.JOIN_APIKEY, join_apikey)
        result, message = notifiers.join_notifier.test_notify(join_id, join_apikey)
        if result:
            return _("join notification succeeded. Check your join clients to make sure it worked")
        else:
            return _("Error sending join notification: {message}").format(message=message)

    @staticmethod
    def testGrowl(host=None, password=None):
        # self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host, default_port=23053)
        password = filters.unhide(sickbeard.GROWL_PASSWORD, password)
        result = notifiers.growl_notifier.test_notify(host, password)

        pw_append = _(" with password") + ": " + password if password else ''
        if result:
            return _("Registered and Tested growl successfully {growl_host}").format(growl_host=unquote_plus(host)) + pw_append
        else:
            return _("Registration and Testing of growl failed {growl_host}").format(growl_host=unquote_plus(host)) + pw_append

    @staticmethod
    def testProwl(prowl_api=None, prowl_priority=0):

        result = notifiers.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return _("Test prowl notice sent successfully")
        else:
            return _("Test prowl notice failed")

    @staticmethod
    def testBoxcar2(accesstoken=None):

        result = notifiers.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return _("Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked")
        else:
            return _("Error sending Boxcar2 notification")

    @staticmethod
    def testPushover(userKey=None, apiKey=None):

        result = notifiers.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return _("Pushover notification succeeded. Check your Pushover clients to make sure it worked")
        else:
            return _("Error sending Pushover notification")

    @staticmethod
    def twitterStep1():
        # noinspection PyProtectedMember
        return notifiers.twitter_notifier._get_authorization()

    @staticmethod
    def twitterStep2(key):

        # noinspection PyProtectedMember
        result = notifiers.twitter_notifier._get_credentials(key)
        logger.log("result: " + str(result))
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
        if not notifiers.twilio_notifier.account_regex.match(sickbeard.TWILIO_ACCOUNT_SID):
            return _('Please enter a valid account sid')

        if not notifiers.twilio_notifier.auth_regex.match(sickbeard.TWILIO_AUTH_TOKEN):
            return _('Please enter a valid auth token')

        if not notifiers.twilio_notifier.phone_regex.match(sickbeard.TWILIO_PHONE_SID):
            return _('Please enter a valid phone sid')

        if not notifiers.twilio_notifier.number_regex.match(sickbeard.TWILIO_TO_NUMBER):
            return _('Please format the phone number as "+1-###-###-####"')

        result = notifiers.twilio_notifier.test_notify()
        if result:
            return _('Authorization successful and number ownership verified')
        else:
            return _('Error sending sms')

    @staticmethod
    def testSlack():
        result = notifiers.slack_notifier.test_notify()
        if result:
            return _("Slack message successful")
        else:
            return _("Slack message failed")

    @staticmethod
    def testMatrix():
        result = notifiers.matrix_notifier.test_notify()
        if result:
            return _("Matrix message successful")
        else:
            return _("Matrix message failed")

    @staticmethod
    def testDiscord():
        result = notifiers.discord_notifier.test_notify()
        if result:
            return _("Discord message successful")
        else:
            return _("Discord message failed")

    @staticmethod
    def testKODI(host=None, username=None, password=None):

        host = config.clean_hosts(host)
        finalResult = ''
        password = filters.unhide(sickbeard.KODI_PASSWORD, password)
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = notifiers.kodi_notifier.test_notify(unquote_plus(curHost), username, password)
            if len(curResult.split(":")) > 2 and 'OK' in curResult.split(":")[2]:
                finalResult += _("Test KODI notice sent successfully to {kodi_host}").format(kodi_host=unquote_plus(curHost))
            else:
                finalResult += _("Test KODI notice failed to {kodi_host}").format(kodi_host=unquote_plus(curHost))
            finalResult += "<br>\n"

        return finalResult

    def testPHT(self, host=None, username=None, password=None):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')

        password = filters.unhide(sickbeard.PLEX_CLIENT_PASSWORD, password)

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = notifiers.plex_notifier.test_notify_pht(unquote_plus(curHost), username, password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += _('Successful test notice sent to Plex Home Theater ... {plex_clients}').format(plex_clients=unquote_plus(curHost))
            else:
                finalResult += _('Test failed for Plex Home Theater ... {plex_clients}').format(plex_clients=unquote_plus(curHost))
            finalResult += '<br>' + '\n'

        ui.notifications.message(_('Tested Plex Home Theater(s)') + ':', unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')

        password = filters.unhide(sickbeard.PLEX_SERVER_PASSWORD, password)

        finalResult = ''

        curResult = notifiers.plex_notifier.test_notify_pms(unquote_plus(host), username, password, plex_server_token)
        if curResult is None:
            finalResult += _('Successful test of Plex Media Server(s) ... {plex_servers}').format(plex_servers=unquote_plus(host.replace(',', ', ')))
        elif curResult is False:
            finalResult += _('Test failed, No Plex Media Server host specified')
        else:
            finalResult += _('Test failed for Plex Media Server(s) ... {plex_servers}').format(plex_servers=unquote_plus(str(curResult).replace(',', ', ')))
        finalResult += '<br>' + '\n'

        ui.notifications.message(_('Tested Plex Media Server host(s)') + ':', unquote_plus(host.replace(',', ', ')))

        return finalResult

    @staticmethod
    def testLibnotify():

        if notifiers.libnotify_notifier.test_notify():
            return _("Tried sending desktop notification via libnotify")
        return notifiers.libnotify_notifier.diagnose()

    @staticmethod
    def testEMBY(host=None, emby_apikey=None):
        host = config.clean_host(host)
        emby_apikey = filters.unhide(sickbeard.EMBY_APIKEY, emby_apikey)
        result = notifiers.emby_notifier.test_notify(unquote_plus(host), emby_apikey)
        if result:
            return _("Test notice sent successfully to {emby_host}").format(emby_host=unquote_plus(host))
        else:
            return _("Test notice failed to {emby_host}").format(emby_host=unquote_plus(host))

    @staticmethod
    def testNMJ(host=None, database=None, mount=None):

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.test_notify(unquote_plus(host), database, mount)
        if result:
            return _("Successfully started the scan update")
        else:
            return _("Test failed to start the scan update")

    @staticmethod
    def settingsNMJ(host=None):

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.notify_settings(unquote_plus(host))
        if result:
            return '{{"message": _("Got settings from {host}"), "database": "{database}", "mount": "{mount}"}}'.format(**{
                "host": host, "database": sickbeard.NMJ_DATABASE, "mount": sickbeard.NMJ_MOUNT
            })
        else:
            # noinspection PyPep8
            return '{"message": _("Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)"), "database": "", "mount": ""}'

    @staticmethod
    def testNMJv2(host=None):

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.test_notify(unquote_plus(host))
        if result:
            return _("Test notice sent successfully to {nmj2_host}").format(nmj2_host=unquote_plus(host))
        else:
            return _("Test notice failed to {nmj2_host}").format(nmj2_host=unquote_plus(host))

    @staticmethod
    def settingsNMJv2(host=None, dbloc=None, instance=None):

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.notify_settings(unquote_plus(host), dbloc, instance)
        if result:
            return '{{"message": _("NMJ Database found at: {host}"), "database": "{database}"}}'.format(
                **{"host": host, "database": sickbeard.NMJv2_DATABASE})
        else:
            # noinspection PyPep8
            return '{{"message": _("Unable to find NMJ Database at location: {dbloc}. Is the right location selected and PCH running?"), "database": ""}}'.format(
                **{
                    "dbloc": dbloc
                })

    @staticmethod
    def getTraktToken(trakt_pin=None):

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return _("Trakt Authorized")
        return _("Trakt Not Authorized!")

    @staticmethod
    def testTrakt(username=None, blacklist_name=None):
        return notifiers.trakt_notifier.test_notify(username, blacklist_name)

    @staticmethod
    def loadShowNotifyLists():

        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            NotifyList = {'emails': '', 'prowlAPIs': ''}
            if r[b'notify_list'] and len(r[b'notify_list']) > 0:
                # First, handle legacy format (emails only)
                if not r[b'notify_list'][0] == '{':
                    NotifyList['emails'] = r[b'notify_list']
                else:
                    NotifyList = dict(ast.literal_eval(r[b'notify_list']))

            data[r[b'show_id']] = {
                'id': r[b'show_id'],
                'name': r[b'show_name'],
                'list': NotifyList['emails'],
                'prowl_notify_list': NotifyList['prowlAPIs']
            }
            size += 1
        data['_size'] = size
        return json.dumps(data)

    @staticmethod
    def saveShowNotifyList(show=None, emails=None, prowlAPIs=None):

        entries = {'emails': '', 'prowlAPIs': ''}
        main_db_con = db.DBConnection()

        # Get current data
        for subs in main_db_con.select("SELECT notify_list FROM tv_shows WHERE show_id = ?", [show]):
            if subs[b'notify_list'] and len(subs[b'notify_list']) > 0:
                # First, handle legacy format (emails only)
                if not subs[b'notify_list'][0] == '{':
                    entries['emails'] = subs[b'notify_list']
                else:
                    entries = dict(ast.literal_eval(subs[b'notify_list']))

        if emails:
            entries['emails'] = emails
        if prowlAPIs:
            entries['prowlAPIs'] = prowlAPIs

        if emails or prowlAPIs:
            if not main_db_con.action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [str(entries), show]):
                return 'ERROR'

        return 'OK'

    @staticmethod
    def testEmail(host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):

        host = config.clean_host(host)
        if notifiers.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return _('Test email sent successfully! Check inbox.')
        else:
            return _('ERROR: {last_error}').format(last_error=notifiers.email_notifier.last_err)

    @staticmethod
    def testPushalot(authorizationToken=None):

        result = notifiers.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return _("Pushalot notification succeeded. Check your Pushalot clients to make sure it worked")
        else:
            return _("Error sending Pushalot notification")

    @staticmethod
    def testPushbullet(api=None):

        result = notifiers.pushbullet_notifier.test_notify(api)
        if result:
            return _("Pushbullet notification succeeded. Check your device to make sure it worked")
        else:
            return _("Error sending Pushbullet notification")

    @staticmethod
    def getPushbulletDevices(api=None):
        # self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

    @staticmethod
    def getPushbulletChannels(api=None):

        result = notifiers.pushbullet_notifier.get_channels(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

    def status(self):
        tvdirFree = helpers.disk_usage_hr(sickbeard.TV_DOWNLOAD_DIR)
        rootDir = {}

        if sickbeard.ROOT_DIRS:
            backend_pieces = sickbeard.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                rootDir[subject] = helpers.disk_usage_hr(subject)

        t = PageTemplate(rh=self, filename="status.mako")
        return t.render(title=_('Status'), header=_('Status'), topmenu='system',
                        tvdirFree=tvdirFree, rootDir=rootDir,
                        controller="home", action="status")

    def shutdown(self, pid=None):
        if not Shutdown.stop(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        title = "Shutting down"
        message = "SickChill is shutting down..."

        return self._genericMessage(title, message)

    def restart(self, pid=None):
        if not Restart.restart(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        t = PageTemplate(rh=self, filename="restart.mako")

        return t.render(title=_("Home"), header=_("Restarting SickChill"), topmenu="system",
                        controller="home", action="restart")

    def updateCheck(self, pid=None):
        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        sickbeard.versionCheckScheduler.action.check_for_new_version(force=True)
        sickbeard.versionCheckScheduler.action.check_for_new_news()

        return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def update(self, pid=None, branch=None):

        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        checkversion = CheckVersion()
        # noinspection PyProtectedMember
        backup = checkversion.updater and checkversion._runbackup()

        if backup is True:
            if branch:
                checkversion.updater.branch = branch

            if checkversion.updater.need_update() and checkversion.updater.update():
                # do a hard restart
                sickbeard.events.put(sickbeard.events.SystemEvent.RESTART)

                t = PageTemplate(rh=self, filename="restart.mako")
                return t.render(title=_("Home"), header=_("Restarting SickChill"), topmenu="home",
                                controller="home", action="restart")
            else:
                return self._genericMessage(_("Update Failed"),
                                            _("Update wasn't successful, not restarting. Check your log for more information."))
        else:
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    @staticmethod
    def fetchRemoteBranches():
        response = []
        try:
            gh_branches = sickbeard.versionCheckScheduler.action.list_remote_branches()
        except GithubException:
            gh_branches = None

        if gh_branches:
            gh_credentials = (sickbeard.GIT_AUTH_TYPE == 0 and sickbeard.GIT_USERNAME and sickbeard.GIT_PASSWORD or
                              sickbeard.GIT_AUTH_TYPE == 1 and sickbeard.GIT_TOKEN)
            for cur_branch in gh_branches:
                branch_obj = {'name': cur_branch}
                if cur_branch == sickbeard.BRANCH:
                    branch_obj['current'] = True

                if cur_branch == 'master' or (gh_credentials and (sickbeard.DEVELOPER == 1 or cur_branch == 'develop')):
                    response.append(branch_obj)

        return json.dumps(response)

    def branchCheckout(self, branch):
        if sickbeard.BRANCH != branch:
            sickbeard.BRANCH = branch
            ui.notifications.message(_('Checking out branch') + ': ', branch)
            return self.update(sickbeard.PID, branch)
        else:
            ui.notifications.message(_('Already on branch') + ': ', branch)
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    @staticmethod
    def getDBcompare():

        checkversion = CheckVersion()
        db_status = checkversion.getDBcompare()

        if db_status == 'upgrade':
            logger.log("Checkout branch has a new DB version - Upgrade", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'upgrade'})
        elif db_status == 'equal':
            logger.log("Checkout branch has the same DB version - Equal", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'equal'})
        elif db_status == 'downgrade':
            logger.log("Checkout branch has an old DB version - Downgrade", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'downgrade'})
        else:
            logger.log("Checkout branch couldn't compare DB version.", logger.ERROR)
            return json.dumps({"status": "error", 'message': 'General exception'})

    def displayShow(self, show=None):
        # todo: add more comprehensive show validation
        try:
            show = int(show)  # fails if show id ends in a period SickChill/SickChill#65
            show_obj = Show.find(sickbeard.showList, show)
        except (ValueError, TypeError):
            return self._genericMessage(_("Error"), _("Invalid show ID: {show}").format(show=str(show)))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC",
            [show_obj.indexerid]
        )

        min_season = (1, 0)[sickbeard.DISPLAY_SHOW_SPECIALS]

        sql_results = main_db_con.select(
            "SELECT * FROM tv_episodes WHERE showid = ? AND season >= ? ORDER BY season DESC, episode DESC",
            [show_obj.indexerid, min_season]
        )

        t = PageTemplate(rh=self, filename="displayShow.mako")
        submenu = [{'title': _('Edit'), 'path': 'home/editShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-pencil'}]

        try:
            showLoc = (show_obj.location, True)
        except ShowDirectoryNotFoundException:
            # noinspection PyProtectedMember
            showLoc = (show_obj._location, False)

        show_message = ''

        if sickbeard.showQueueScheduler.action.is_being_added(show_obj):
            show_message = _('This show is in the process of being downloaded - the info below is incomplete.')

        elif sickbeard.showQueueScheduler.action.is_being_updated(show_obj):
            show_message = _('The information on this page is in the process of being updated.')

        elif sickbeard.showQueueScheduler.action.is_being_refreshed(show_obj):
            show_message = _('The episodes below are currently being refreshed from disk')

        elif sickbeard.showQueueScheduler.action.is_being_subtitled(show_obj):
            show_message = _('Currently downloading subtitles for this show')

        elif sickbeard.showQueueScheduler.action.is_in_refresh_queue(show_obj):
            show_message = _('This show is queued to be refreshed.')

        elif sickbeard.showQueueScheduler.action.is_in_update_queue(show_obj):
            show_message = _('This show is queued and awaiting an update.')

        elif sickbeard.showQueueScheduler.action.is_in_subtitle_queue(show_obj):
            show_message = _('This show is queued and awaiting subtitles download.')

        if not sickbeard.showQueueScheduler.action.is_being_added(show_obj):
            if not sickbeard.showQueueScheduler.action.is_being_updated(show_obj):
                if show_obj.paused:
                    submenu.append({'title': _('Resume'), 'path': 'home/togglePause?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-play'})
                else:
                    submenu.append({'title': _('Pause'), 'path': 'home/togglePause?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-pause'})

                # noinspection PyPep8
                submenu.append({
                                   'title': _('Remove'),
                                   'path': 'home/deleteShow?show={0:d}'.format(show_obj.indexerid),
                                   'class': 'removeshow',
                                   'confirm': True,
                                   'icon': 'fa fa-trash'
                                   })
                submenu.append({'title': _('Re-scan files'), 'path': 'home/refreshShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-refresh'})
                # noinspection PyPep8
                submenu.append(
                    {'title': _('Force Full Update'), 'path': 'home/updateShow?show={0:d}&amp;force=1'.format(show_obj.indexerid), 'icon': 'fa fa-exchange'})
                # noinspection PyPep8
                submenu.append({
                                   'title': _('Update show in KODI'),
                                   'path': 'home/updateKODI?show={0:d}'.format(show_obj.indexerid),
                                   'requires': self.haveKODI(),
                                   'icon': 'menu-icon-kodi'
                                   })
                # noinspection PyPep8
                submenu.append({
                                   'title': _('Update show in Emby'),
                                   'path': 'home/updateEMBY?show={0:d}'.format(show_obj.indexerid),
                                   'requires': self.haveEMBY(),
                                   'icon': 'menu-icon-emby'
                                   })
                if seasonResults and int(seasonResults[-1][b"season"]) == 0:
                    if sickbeard.DISPLAY_SHOW_SPECIALS:
                        # noinspection PyPep8
                        submenu.append({
                                           'title': _('Hide specials'),
                                           'path': 'home/toggleDisplayShowSpecials/?show={0:d}'.format(show_obj.indexerid),
                                           'confirm': True,
                                           'icon': 'fa fa-times'
                                           })
                    else:
                        # noinspection PyPep8
                        submenu.append({
                                           'title': _('Show specials'),
                                           'path': 'home/toggleDisplayShowSpecials/?show={0:d}'.format(show_obj.indexerid),
                                           'confirm': True,
                                           'icon': 'fa fa-check'
                                           })

                submenu.append({'title': _('Preview Rename'), 'path': 'home/testRename?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-tag'})

                if sickbeard.USE_SUBTITLES and show_obj.subtitles and not sickbeard.showQueueScheduler.action.is_being_subtitled(show_obj):
                    # noinspection PyPep8
                    submenu.append(
                        {'title': _('Download Subtitles'), 'path': 'home/subtitleShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-language'})

        epCounts = {
            Overview.SKIPPED: 0,
            Overview.WANTED: 0,
            Overview.QUAL: 0,
            Overview.GOOD: 0,
            Overview.UNAIRED: 0,
            Overview.SNATCHED: 0,
            Overview.SNATCHED_PROPER: 0,
            Overview.SNATCHED_BEST: 0
        }
        epCats = {}

        for curResult in sql_results:
            curEpCat = show_obj.getOverview(curResult[b"status"])
            if curEpCat:
                epCats[str(curResult[b"season"]) + "x" + str(curResult[b"episode"])] = curEpCat
                epCounts[curEpCat] += 1

        if sickbeard.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickbeard.showList:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            sortedShowLists = [
                ["Shows", sorted(shows, key=lambda mbr: attrgetter('sort_name')(mbr))],
                ["Anime", sorted(anime, key=lambda mbr: attrgetter('sort_name')(mbr))]
            ]
        else:
            sortedShowLists = [
                ["Shows", sorted(sickbeard.showList, key=lambda mbr: attrgetter('sort_name')(mbr))]
            ]

        bwl = None
        if show_obj.is_anime:
            bwl = show_obj.release_groups

        show_obj.exceptions = sickbeard.scene_exceptions.get_scene_exceptions(show_obj.indexerid)

        indexerid = int(show_obj.indexerid)
        indexer = int(show_obj.indexer)

        # Delete any previous occurrences
        for index, recentShow in enumerate(sickbeard.SHOWS_RECENT):
            if recentShow['indexerid'] == indexerid:
                del sickbeard.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del sickbeard.SHOWS_RECENT[4:]

        # Insert most recent show
        sickbeard.SHOWS_RECENT.insert(0, {
            'indexerid': indexerid,
            'name': show_obj.name,
        })

        return t.render(
            submenu=submenu, showLoc=showLoc, show_message=show_message,
            show=show_obj, sql_results=sql_results, seasonResults=seasonResults,
            sortedShowLists=sortedShowLists, bwl=bwl, epCounts=epCounts,
            epCats=epCats, all_scene_exceptions=show_obj.exceptions,
            scene_numbering=get_scene_numbering_for_show(indexerid, indexer),
            xem_numbering=get_xem_numbering_for_show(indexerid, indexer),
            scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexerid, indexer),
            xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexerid, indexer),
            title=show_obj.name,
            controller="home",
            action="displayShow"
        )

    @staticmethod
    def plotDetails(show, season, episode):
        main_db_con = db.DBConnection()
        result = main_db_con.select_one(
            "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?", (int(show), int(season), int(episode)))
        return result[b'description'] if result else 'Episode not found.'

    @staticmethod
    def sceneExceptions(show):
        exceptionsList = sickbeard.scene_exceptions.get_all_scene_exceptions(show)
        if not exceptionsList:
            return _("No scene exceptions")

        out = []
        for season, exceptions in iter(sorted(six.iteritems(exceptionsList))):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(exceptions.names))
        return "<br>".join(out)

    def editShow(self, show=None, location=None, anyQualities=None, bestQualities=None,
                 exceptions_list=None, season_folders=None, paused=None, directCall=False,
                 air_by_date=None, sports=None, dvdorder=None, indexerLang=None,
                 subtitles=None, subtitles_sr_metadata=None, rls_ignore_words=None, rls_require_words=None, rls_prefer_words=None,
                 anime=None, blacklist=None, whitelist=None, scene=None,
                 defaultEpStatus=None, quality_preset=None):

        anidb_failed = False

        try:
            show_obj = Show.find(sickbeard.showList, int(show))
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

        show_obj.exceptions = sickbeard.scene_exceptions.get_all_scene_exceptions(show_obj.indexerid)

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC",
            [show_obj.indexerid]
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
                        anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=show_obj.name)
                        groups = anime.get_groups()
                    except Exception as e:
                        ui.notifications.error(_('Unable to retreive Fansub Groups from AniDB.'))
                        logger.log('Unable to retreive Fansub Groups from AniDB. Error is {0}'.format(e), logger.DEBUG)

            with show_obj.lock:
                show = show_obj

            if show_obj.is_anime:
                return t.render(show=show, scene_exceptions=show_obj.exceptions, seasonResults=seasonResults,
                                groups=groups, whitelist=whitelist, blacklist=blacklist,
                                title=_('Edit Show'), header=_('Edit Show'), controller="home", action="editShow")
            else:
                return t.render(show=show, scene_exceptions=show_obj.exceptions, seasonResults=seasonResults,
                                title=_('Edit Show'), header=_('Edit Show'), controller="home", action="editShow")

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
            if len(exceptions_list) > 0:
                exceptions_list = exceptions_list[0]
            else:
                exceptions_list = None

        # Map custom exceptions
        exceptions = {}

        if exceptions_list is not None:
            # noinspection PyUnresolvedReferences
            for season in exceptions_list.split(','):
                (season, shows) = season.split(':')

                show_list = []

                for cur_show in shows.split('|'):
                    show_list.append({'show_name': unquote_plus(cur_show), 'custom': True})

                exceptions[int(season)] = show_list

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
                    sickbeard.showQueueScheduler.action.refresh_show(show_obj)
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

            if not isinstance(location, six.text_type):
                location = ek(six.text_type, location, 'utf-8')

            location = ek(os.path.normpath, xhtml_unescape(location))
            # noinspection PyProtectedMember
            old_location = ek(os.path.normpath, show_obj._location)
            # if we change location clear the db of episodes, change it, write to db, and rescan
            if old_location != location:
                logger.log(old_location + " != " + location, logger.DEBUG)
                if not (ek(os.path.isdir, location) or sickbeard.CREATE_MISSING_SHOW_DIRS or sickbeard.ADD_SHOWS_WO_DIR):
                    errors.append(_("New location <tt>{location}</tt> does not exist").format(location=location))
                else:
                    # change it
                    try:
                        show_obj.location = location
                        try:
                            sickbeard.showQueueScheduler.action.refresh_show(show_obj)
                        except CantRefreshShowException as e:
                            errors.append(_("Unable to refresh this show: {error}").format(error=e))
                            # grab updated info from TVDB
                            # show_obj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        # noinspection PyPep8
                        errors.append(
                            "The folder at <tt>{0}</tt> doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SickChill.".format(
                                location))

            # save it to the DB
            show_obj.saveToDB()

        # force the update
        if do_update:
            try:
                sickbeard.showQueueScheduler.action.update_show(show_obj, True)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {error}").format(error=e))

        try:
            sickbeard.scene_exceptions.update_scene_exceptions(show_obj.indexerid, exceptions)  # @UndefinedVdexerid)
            time.sleep(cpu_presets[sickbeard.CPU_PRESET])
        except CantUpdateShowException:
            errors.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                sickbeard.scene_numbering.xem_refresh(show_obj.indexerid, show_obj.indexer)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException:
                errors.append(_("Unable to force an update on scene numbering of the show."))

        if directCall:
            return errors

        if errors:
            ui.notifications.error(
                _('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"),
                '<ul>' + '\n'.join(['<li>{0}</li>'.format(error) for error in errors]) + "</ul>"
            )

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = Show.pause(show)

        if error:
            return self._genericMessage(_('Error'), error)

        ui.notifications.message(
            _('{show_name} has been {paused_resumed}').format(show_name=show.name, paused_resumed=(_('resumed'), _('paused'))[show.paused])
        )

        return self.redirect("/home/displayShow?show={0:d}".format(show.indexerid))

    def deleteShow(self, show=None, full=0):
        if show:
            error, show = Show.delete(show, full)

            if error:
                return self._genericMessage(_('Error'), error)

            ui.notifications.message(
                _('{show_name} has been {deleted_trashed} {was_deleted}').format(
                    show_name=show.name,
                    deleted_trashed=(_('deleted'), _('trashed'))[sickbeard.TRASH_REMOVE_SHOW],
                    was_deleted=(_('(media untouched)'), _('(with all related media)'))[bool(full)]
                )
            )

            time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        # Remove show from 'RECENT SHOWS' in 'Shows' menu
        sickbeard.SHOWS_RECENT = [x for x in sickbeard.SHOWS_RECENT if x['indexerid'] != show.indexerid]

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        error, show = Show.refresh(show)

        # This is a show validation error
        if error and not show:
            return self._genericMessage(_('Error'), error)

        # This is a refresh error
        if error:
            ui.notifications.error(_('Unable to refresh this show.'), error)

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show.indexerid))

    def updateShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            sickbeard.showQueueScheduler.action.update_show(show_obj, bool(force))
        except CantUpdateShowException as e:
            ui.notifications.error(_("Unable to update this show."), ex(e))

        # just give it some time
        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        sickbeard.showQueueScheduler.action.download_subtitles(show_obj, bool(force))

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        show_obj = None

        if show:
            show_obj = Show.find(sickbeard.showList, int(show))
            if show_obj:
                showName = urllib.parse.quote_plus(show_obj.name.encode('utf-8'))

        if sickbeard.KODI_UPDATE_ONLYFIRST:
            host = sickbeard.KODI_HOST.split(",")[0].strip()
        else:
            host = sickbeard.KODI_HOST

        if notifiers.kodi_notifier.update_library(showName=showName):
            ui.notifications.message(_("Library update command sent to KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))
        else:
            ui.notifications.error(_("Unable to contact one or more KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is notifiers.plex_notifier.update_library():
            ui.notifications.message(_("Library update command sent to Plex Media Server host: {plex_server}").format
                                     (plex_server=sickbeard.PLEX_SERVER_HOST))
        else:
            ui.notifications.error(_("Unable to contact Plex Media Server host: {plex_server}").format
                                   (plex_server=sickbeard.PLEX_SERVER_HOST))
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        show_obj = None

        if show:
            show_obj = Show.find(sickbeard.showList, int(show))

        if notifiers.emby_notifier.update_library(show_obj):
            ui.notifications.message(
                _("Library update command sent to Emby host: {emby_host}").format(emby_host=sickbeard.EMBY_HOST))
        else:
            ui.notifications.error(_("Unable to contact Emby host: {emby_host}").format(emby_host=sickbeard.EMBY_HOST))

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.indexerid))
        else:
            return self.redirect('/home/')

    def setStatus(self, show=None, eps=None, status=None, direct=False):

        if not all([show, eps, status]):
            errMsg = _("You must specify a show and at least one episode")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        # Use .has_key() since it is overridden for statusStrings in common.py
        if status not in statusStrings:
            errMsg = _("Invalid status")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            errMsg = _("Show not in show list")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        segments = {}
        if eps:
            trakt_data = []
            sql_l = []
            for cur_ep in eps.split('|'):

                if not cur_ep:
                    logger.log("cur_ep was empty when trying to setStatus", logger.DEBUG)

                logger.log("Attempting to set status on episode " + cur_ep + " to " + status, logger.DEBUG)

                epInfo = cur_ep.split('x')

                if not all(epInfo):
                    logger.log("Something went wrong when trying to setStatus, epInfo[0]: {0}, epInfo[1]: {1}".format(epInfo[0], epInfo[1]), logger.DEBUG)
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
                        logger.log("Refusing to change status of " + cur_ep + " because it is UNAIRED", logger.WARNING)
                        continue

                    if int(status) in Quality.DOWNLOADED and ep_obj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + \
                        Quality.DOWNLOADED + [IGNORED] and not ek(os.path.isfile, ep_obj.location):
                        logger.log("Refusing to change status of " + cur_ep + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED", logger.WARNING)
                        continue

                    if int(status) == FAILED and ep_obj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + \
                        Quality.DOWNLOADED + Quality.ARCHIVED:
                        logger.log("Refusing to change status of " + cur_ep + " to FAILED because it's not SNATCHED/DOWNLOADED", logger.WARNING)
                        continue

                    if ep_obj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        logger.log(
                            "Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        ep_obj.release_name = ""

                    ep_obj.status = int(status)

                    # mass add to database
                    sql_l.append(ep_obj.get_sql())

                    if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
                        trakt_data.append((ep_obj.season, ep_obj.episode))

            if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
                data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)
                if data['seasons']:
                    upd = ""
                    if int(status) in [WANTED, FAILED]:
                        logger.log(
                            "Add episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " to Watchlist", logger.DEBUG
                        )
                        upd = "add"
                    elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                        # noinspection PyPep8
                        logger.log(
                            "Remove episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " from Watchlist", logger.DEBUG
                        )
                        upd = "remove"

                    if upd:
                        notifiers.trakt_notifier.update_watchlist(show_obj, data_episode=data, update=upd)

            if sql_l:
                main_db_con = db.DBConnection()
                main_db_con.mass_action(sql_l)

        if int(status) == WANTED and not show_obj.paused:
            msg = _("Backlog was automatically started for the following seasons of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ':<br><ul>'

            for season, segment in six.iteritems(segments):
                cur_backlog_queue_item = search_queue.BacklogQueueItem(show_obj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.log("Sending backlog for " + show_obj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Backlog started"), msg)
        elif int(status) == WANTED and show_obj.paused:
            logger.log("Some episodes were set to wanted, but " + show_obj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = _("Retrying Search was automatically started for the following season of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ':<br><ul>'

            for season, segment in six.iteritems(segments):
                cur_failed_queue_item = search_queue.FailedQueueItem(show_obj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_failed_queue_item)

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.log("Retrying Search for " + show_obj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Retry Search started"), msg)

        if direct:
            return json.dumps({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def testRename(self, show=None):

        if not show:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        ep_obj_list = show_obj.getAllEpisodes(has_location=True)
        ep_obj_list = [x for x in ep_obj_list if x.location]
        ep_obj_rename_list = []
        for ep_obj in ep_obj_list:
            has_already = False
            for check in ep_obj.relatedEps + [ep_obj]:
                if check in ep_obj_rename_list:
                    has_already = True
                    break
            if not has_already:
                ep_obj_rename_list.append(ep_obj)

        if ep_obj_rename_list:
            ep_obj_rename_list.reverse()

        t = PageTemplate(rh=self, filename="testRename.mako")
        submenu = [{'title': _('Edit'), 'path': 'home/editShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'ui-icon ui-icon-pencil'}]

        return t.render(submenu=submenu, ep_obj_list=ep_obj_rename_list,
                        show=show_obj, title=_('Preview Rename'),
                        header=_('Preview Rename'),
                        controller="home", action="previewRename")

    def doRename(self, show=None, eps=None):
        if not (show and eps):
            return self._genericMessage(_("Error"), _("You must specify a show and at least one episode"))

        show_obj = Show.find(sickbeard.showList, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if not eps:
            return self.redirect("/home/displayShow?show=" + show)

        main_db_con = db.DBConnection()
        for cur_ep in eps.split('|'):

            epInfo = cur_ep.split('x')

            # this is probably the worst possible way to deal with double eps but I've kinda painted myself into a corner here with this stupid database
            ep_result = main_db_con.select(
                "SELECT location FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND 5=5",
                [show, epInfo[0], epInfo[1]])
            if not ep_result:
                logger.log("Unable to find an episode for " + cur_ep + ", skipping", logger.WARNING)
                continue
            related_eps_result = main_db_con.select(
                "SELECT season, episode FROM tv_episodes WHERE location = ? AND episode != ?",
                [ep_result[0][b"location"], epInfo[1]]
            )

            root_ep_obj = show_obj.getEpisode(epInfo[0], epInfo[1])
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(cur_related_ep[b"season"], cur_related_ep[b"episode"])
                if related_ep_obj not in root_ep_obj.relatedEps:
                    root_ep_obj.relatedEps.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    # def searchEpisodeListManual(self, show=None, season=None, episode=None, search_mode='eponly'):
    #     # retrieve the episode object and fail if we can't get one
    #     self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
    #     self.set_header(b'Content-Type', 'application/json')
    #     ep_obj, error_msg = self._getEpisode(show, season, episode)
    #     if error_msg or not ep_obj:
    #         return json.dumps({'result': 'failure', 'errorMessage': error_msg})
    #
    #     return search.searchProvidersList(ep_obj.show, ep_obj, search_mode)
    #
    # def snatchEpisodeManual(self, result_dict):
    #     self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
    #     self.set_header(b'Content-Type', 'application/json')
    #     result = sickbeard.classes.TorrentSearchResult.make_result(result_dict)
    #     return search.snatchEpisode(result, SNATCHED_BEST)
    #
    # def testSearchEpisodeListManual(self, show=None, season=None, episode=None, search_mode='eponly'):
    #     r = self.searchEpisodeListManual(show, season, episode, search_mode)
    #     self.snatchEpisodeManual(r.get('results')[0])

    def searchEpisode(self, show=None, season=None, episode=None, downCurQuality=0):

        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(ep_obj.show, ep_obj, bool(int(downCurQuality)))

        sickbeard.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps(
                {'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({'result': 'success'})
        else:
            return json.dumps({'result': 'failure'})

    # ## Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(search_thread, search_status):
            results = []
            show_obj = Show.find(sickbeard.showList, int(search_thread.show.indexerid))

            if not show_obj:
                logger.log('No Show Object found for show with indexerID: ' + str(search_thread.show.indexerid), logger.WARNING)
                return results

            # noinspection PyProtectedMember
            def relative_ep_location(ep_loc, show_loc):
                """ Returns the relative location compared to the show's location """
                if ep_loc and show_loc and ep_loc.lower().startswith(show_loc.lower()):
                    return ep_loc[len(show_loc) + 1:]
                else:
                    return ep_loc

            if isinstance(search_thread, sickbeard.search_queue.ManualSearchQueueItem):
                # noinspection PyProtectedMember
                results.append({
                    'show': search_thread.show.indexerid,
                    'episode': search_thread.segment.episode,
                    'episodeindexid': search_thread.segment.indexerid,
                    'season': search_thread.segment.season,
                    'searchstatus': search_status,
                    'status': statusStrings[search_thread.segment.status],
                    'quality': self.getQualityClass(search_thread.segment),
                    'overview': Overview.overviewStrings[show_obj.getOverview(search_thread.segment.status)],
                    'location': relative_ep_location(search_thread.segment._location, show_obj._location),
                    'size': pretty_file_size(search_thread.segment.file_size) if search_thread.segment.file_size else ''
                })
            else:
                for ep_obj in search_thread.segment:
                    # noinspection PyProtectedMember
                    results.append({
                        'show': ep_obj.show.indexerid,
                        'episode': ep_obj.episode,
                        'episodeindexid': ep_obj.indexerid,
                        'season': ep_obj.season,
                        'searchstatus': search_status,
                        'status': statusStrings[ep_obj.status],
                        'quality': self.getQualityClass(ep_obj),
                        'overview': Overview.overviewStrings[show_obj.getOverview(ep_obj.status)],
                        'location': relative_ep_location(ep_obj._location, show_obj._location),
                        'size': pretty_file_size(ep_obj.file_size) if ep_obj.file_size else ''
                    })

            return results

        episodes = []

        # Queued Searches
        searchstatus = 'Queued'
        for searchThread in sickbeard.searchQueueScheduler.action.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = 'Searching'
        if sickbeard.searchQueueScheduler.action.is_manualsearch_in_progress():
            searchThread = sickbeard.searchQueueScheduler.action.currentItem

            if searchThread.success:
                searchstatus = 'Finished'

            episodes += getEpisodes(searchThread, searchstatus)

        # Finished Searches
        searchstatus = 'Finished'
        for searchThread in sickbeard.search_queue.MANUAL_SEARCH_HISTORY:
            if show and str(searchThread.show.indexerid) != show:
                continue

            if isinstance(searchThread, sickbeard.search_queue.ManualSearchQueueItem):
                # noinspection PyTypeChecker
                if not [x for x in episodes if x['episodeindexid'] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                # ## These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segment/episodes
                # TODO: WTF is this doing? Intensive
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j['episodeindexid']]:
                    episodes += getEpisodes(searchThread, searchstatus)

        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header(b'Content-Type', 'application/json')
        return json.dumps({'episodes': episodes})

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
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        # noinspection PyBroadException
        try:
            new_subtitles = ep_obj.download_subtitles()  # pylint: disable=no-member
        except Exception:
            return json.dumps({'result': 'failure'})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _('New subtitles downloaded: {new_subtitle_languages}').format(
                new_subtitle_languages=', '.join(new_languages))
        else:
            status = _('No subtitles downloaded')

        ui.notifications.message(ep_obj.show.name, status)  # pylint: disable=no-member
        return json.dumps({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})  # pylint: disable=no-member

    def retrySearchSubtitles(self, show, season, episode, lang):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        try:
            new_subtitles = ep_obj.download_subtitles(force_lang=lang)
        except Exception as error:
            return json.dumps({'result': 'failure', 'errorMessage': error.message})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _('New subtitles downloaded: {new_subtitle_languages}').format(
                new_subtitle_languages=', '.join(new_languages))
        else:
            status = _('No subtitles downloaded')

        ui.notifications.message(ep_obj.show.name, status)
        return json.dumps({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})

    def setSceneNumbering(self, show, indexer, forSeason=None, forEpisode=None, forAbsolute=None, sceneSeason=None,
                          sceneEpisode=None, sceneAbsolute=None):

        # sanitize:
        if forSeason in ('null', ''):
            forSeason = None
        if forEpisode in ('null', ''):
            forEpisode = None
        if forAbsolute in ('null', ''):
            forAbsolute = None
        if sceneSeason in ('null', ''):
            sceneSeason = None
        if sceneEpisode in ('null', ''):
            sceneEpisode = None
        if sceneAbsolute in ('null', ''):
            sceneAbsolute = None

        show_obj = Show.find(sickbeard.showList, int(show))

        if show_obj.is_anime:
            result = {
                'success': True,
                'forAbsolute': forAbsolute,
            }
        else:
            result = {
                'success': True,
                'forSeason': forSeason,
                'forEpisode': forEpisode,
            }

        # retrieve the episode object and fail if we can't get one
        if show_obj.is_anime:
            ep_obj, error_msg = self._getEpisode(show, absolute=forAbsolute)
        else:
            ep_obj, error_msg = self._getEpisode(show, forSeason, forEpisode)

        if error_msg or not ep_obj:
            result[b'success'] = False
            result[b'errorMessage'] = error_msg
        elif show_obj.is_anime:
            logger.log("setAbsoluteSceneNumbering for {0} from {1} to {2}".format(show, forAbsolute, sceneAbsolute), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            logger.log("setEpisodeSceneNumbering for {0} from {1}x{2} to {3}x{4}".format(show, forSeason, forEpisode, sceneSeason, sceneEpisode), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forSeason = int(forSeason)
            forEpisode = int(forEpisode)
            if sceneSeason is not None:
                sceneSeason = int(sceneSeason)
            if sceneEpisode is not None:
                sceneEpisode = int(sceneEpisode)

            set_scene_numbering(show, indexer, season=forSeason, episode=forEpisode, sceneSeason=sceneSeason,
                                sceneEpisode=sceneEpisode)

        if show_obj.is_anime:
            sn = get_scene_absolute_numbering(show, indexer, forAbsolute)
            if sn:
                result[b'sceneAbsolute'] = sn
            else:
                result[b'sceneAbsolute'] = None
        else:
            sn = get_scene_numbering(show, indexer, forSeason, forEpisode)
            if sn:
                (result[b'sceneSeason'], result[b'sceneEpisode']) = sn
            else:
                (result[b'sceneSeason'], result[b'sceneEpisode']) = (None, None)

        return json.dumps(result)

    def retryEpisode(self, show, season, episode, downCurQuality=0):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.FailedQueueItem(ep_obj.show, [ep_obj], bool(int(downCurQuality)))
        sickbeard.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps(
                {'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({'result': 'success'})
        else:
            return json.dumps({'result': 'failure'})

    @staticmethod
    def fetch_releasegroups(show_name):
        logger.log('ReleaseGroups: {0}'.format(show_name), logger.INFO)
        if helpers.set_up_anidb_connection():
            try:
                anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=show_name)
                groups = anime.get_groups()
                logger.log('ReleaseGroups: {0}'.format(groups), logger.INFO)
                return json.dumps({'result': 'success', 'groups': groups})
            except AttributeError as error:
                logger.log('Unable to get ReleaseGroups: {0}'.format(error), logger.DEBUG)

        return json.dumps({'result': 'failure'})
