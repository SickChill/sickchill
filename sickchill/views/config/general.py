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
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import gettext
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import config, filters, helpers, logger, ui
from sickbeard.common import Quality, WANTED
from sickchill.helper import setup_github, try_int
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from .index import Config


@Route('/config/general(/?.*)', name='config:general')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_general.mako")

        return t.render(title=_('Config - General'), header=_('General Configuration'),
                        topmenu='config', submenu=self.ConfigMenu(),
                        controller="config", action="index")

    @staticmethod
    def generateApiKey():
        return helpers.generateApiKey()

    @staticmethod
    def saveRootDirs(rootDirString=None):
        sickbeard.ROOT_DIRS = rootDirString

    @staticmethod
    def saveAddShowDefaults(defaultStatus, anyQualities, bestQualities, defaultSeasonFolders, subtitles=False,
                            anime=False, scene=False, defaultStatusAfter=WANTED):

        if anyQualities:
            anyQualities = anyQualities.split(',')
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(',')
        else:
            bestQualities = []

        newQuality = Quality.combineQualities([int(quality) for quality in anyQualities], [int(quality) for quality in bestQualities])

        sickbeard.STATUS_DEFAULT = int(defaultStatus)
        sickbeard.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        sickbeard.QUALITY_DEFAULT = int(newQuality)

        sickbeard.SEASON_FOLDERS_DEFAULT = config.checkbox_to_value(defaultSeasonFolders)
        sickbeard.SUBTITLES_DEFAULT = config.checkbox_to_value(subtitles)

        sickbeard.ANIME_DEFAULT = config.checkbox_to_value(anime)

        sickbeard.SCENE_DEFAULT = config.checkbox_to_value(scene)
        sickbeard.save_config()

        ui.notifications.message(_('Saved Defaults'), _('Your "add show" defaults have been set to your current selections.'))

    def saveGeneral(
            self, log_dir=None, log_nr=5, log_size=1, web_port=None, notify_on_login=None, web_log=None, encryption_version=None, web_ipv6=None,
            trash_remove_show=None, trash_rotate_logs=None, update_frequency=None, skip_removed_files=None,
            indexerDefaultLang='en', ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3, web_username=None,
            api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL',
            web_password=None, version_notify=None, enable_https=None, https_cert=None, https_key=None,
            handle_reverse_proxy=None, sort_article=None, auto_update=None, notify_on_update=None,
            proxy_setting=None, proxy_indexers=None, anon_redirect=None, git_path=None, git_remote=None,
            calendar_unprotected=None, calendar_icons=None, debug=None, ssl_verify=None, no_restart=None, coming_eps_missed_range=None,
            fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None, time_preset=None,
            indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None, fanart_background=None, fanart_background_opacity=None,
            sickchill_background=None, sickchill_background_path=None, custom_css=None, custom_css_path=None,
            git_reset=None, git_auth_type=0, git_username=None, git_password=None, git_token=None,
            display_all_seasons=None, gui_language=None, ignore_broken_symlinks=None):

        results = []

        if gui_language != sickbeard.GUI_LANG:
            if gui_language:
                # Selected language
                gettext.translation('messages', sickbeard.LOCALE_DIR, languages=[gui_language], codeset='UTF-8').install(unicode=1, names=["ngettext"])
            else:
                # System default language
                gettext.install('messages', sickbeard.LOCALE_DIR, unicode=1, codeset='UTF-8', names=["ngettext"])

            sickbeard.GUI_LANG = gui_language

        # Misc
        sickbeard.DOWNLOAD_URL = download_url
        sickbeard.INDEXER_DEFAULT_LANGUAGE = indexerDefaultLang
        sickbeard.EP_DEFAULT_DELETED_STATUS = ep_default_deleted_status
        sickbeard.SKIP_REMOVED_FILES = config.checkbox_to_value(skip_removed_files)
        sickbeard.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        config.change_showupdate_hour(showupdate_hour)
        config.change_version_notify(version_notify)
        sickbeard.AUTO_UPDATE = config.checkbox_to_value(auto_update)
        sickbeard.NOTIFY_ON_UPDATE = config.checkbox_to_value(notify_on_update)
        # sickbeard.LOG_DIR is set in config.change_log_dir()
        sickbeard.LOG_NR = log_nr
        sickbeard.LOG_SIZE = float(log_size)

        sickbeard.TRASH_REMOVE_SHOW = config.checkbox_to_value(trash_remove_show)
        sickbeard.TRASH_ROTATE_LOGS = config.checkbox_to_value(trash_rotate_logs)
        sickbeard.IGNORE_BROKEN_SYMLINKS = config.checkbox_to_value(ignore_broken_symlinks)
        config.change_update_frequency(update_frequency)
        sickbeard.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        sickbeard.SORT_ARTICLE = config.checkbox_to_value(sort_article)
        sickbeard.CPU_PRESET = cpu_preset
        sickbeard.ANON_REDIRECT = anon_redirect
        sickbeard.PROXY_SETTING = proxy_setting
        sickbeard.PROXY_INDEXERS = config.checkbox_to_value(proxy_indexers)

        sickbeard.GIT_AUTH_TYPE = int(git_auth_type)
        sickbeard.GIT_USERNAME = git_username
        sickbeard.GIT_PASSWORD = filters.unhide(sickbeard.GIT_PASSWORD, git_password)
        sickbeard.GIT_TOKEN = filters.unhide(sickbeard.GIT_TOKEN, git_token)

        # noinspection PyPep8
        if (sickbeard.GIT_AUTH_TYPE, sickbeard.GIT_USERNAME, sickbeard.GIT_PASSWORD, sickbeard.GIT_TOKEN) != (git_auth_type, git_username, git_password, git_token):
            # Re-Initializes sickbeard.gh, so a restart isn't necessary
            setup_github()

        # sickbeard.GIT_RESET = config.checkbox_to_value(git_reset)
        # Force GIT_RESET
        sickbeard.GIT_RESET = 1
        sickbeard.GIT_PATH = git_path
        sickbeard.GIT_REMOTE = git_remote
        sickbeard.CALENDAR_UNPROTECTED = config.checkbox_to_value(calendar_unprotected)
        sickbeard.CALENDAR_ICONS = config.checkbox_to_value(calendar_icons)
        sickbeard.NO_RESTART = config.checkbox_to_value(no_restart)
        sickbeard.DEBUG = config.checkbox_to_value(debug)
        logger.set_level()

        sickbeard.SSL_VERIFY = config.checkbox_to_value(ssl_verify)
        # sickbeard.LOG_DIR is set in config.change_log_dir()

        sickbeard.COMING_EPS_MISSED_RANGE = config.min_max(coming_eps_missed_range, 7, 0, 42810)

        sickbeard.DISPLAY_ALL_SEASONS = config.checkbox_to_value(display_all_seasons)
        sickbeard.NOTIFY_ON_LOGIN = config.checkbox_to_value(notify_on_login)
        sickbeard.WEB_PORT = try_int(web_port)
        sickbeard.WEB_IPV6 = config.checkbox_to_value(web_ipv6)
        # sickbeard.WEB_LOG is set in config.change_log_dir()
        sickbeard.ENCRYPTION_VERSION = config.checkbox_to_value(encryption_version, value_on=2, value_off=0)
        sickbeard.WEB_USERNAME = web_username
        sickbeard.WEB_PASSWORD = filters.unhide(sickbeard.WEB_PASSWORD, web_password)

        sickbeard.FUZZY_DATING = config.checkbox_to_value(fuzzy_dating)
        sickbeard.TRIM_ZERO = config.checkbox_to_value(trim_zero)

        if date_preset:
            sickbeard.DATE_PRESET = date_preset

        if indexer_default:
            sickbeard.INDEXER_DEFAULT = try_int(indexer_default)

        if indexer_timeout:
            sickbeard.INDEXER_TIMEOUT = try_int(indexer_timeout)

        if time_preset:
            sickbeard.TIME_PRESET_W_SECONDS = time_preset
            sickbeard.TIME_PRESET = time_preset.replace(":%S", "")

        sickbeard.TIMEZONE_DISPLAY = timezone_display

        if not config.change_log_dir(log_dir, web_log):
            results += [
                _("Unable to create directory {directory}, log directory not changed.").format(directory=ek(os.path.normpath, log_dir))]

        sickbeard.API_KEY = api_key

        sickbeard.ENABLE_HTTPS = config.checkbox_to_value(enable_https)

        if not config.change_https_cert(https_cert):
            results += [
                _("Unable to create directory {directory}, https cert directory not changed.").format(directory=ek(os.path.normpath, https_cert))]

        if not config.change_https_key(https_key):
            results += [
                _("Unable to create directory {directory}, https key directory not changed.").format(directory=ek(os.path.normpath, https_key))]

        sickbeard.HANDLE_REVERSE_PROXY = config.checkbox_to_value(handle_reverse_proxy)

        sickbeard.THEME_NAME = theme_name
        sickbeard.SICKCHILL_BACKGROUND = config.checkbox_to_value(sickchill_background)
        config.change_sickchill_background(sickchill_background_path)
        sickbeard.FANART_BACKGROUND = config.checkbox_to_value(fanart_background)
        sickbeard.FANART_BACKGROUND_OPACITY = fanart_background_opacity
        sickbeard.CUSTOM_CSS = config.checkbox_to_value(custom_css)
        config.change_custom_css(custom_css_path)

        sickbeard.DEFAULT_PAGE = default_page

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/general/")
