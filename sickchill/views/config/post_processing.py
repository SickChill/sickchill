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

from __future__ import print_function, unicode_literals

import os

from tornado.web import addslash

import sickbeard
from sickbeard import config, logger, naming, ui
from sickbeard.common import NAMING_LIMITED_EXTEND_E_PREFIXED
from sickchill.helper import try_int
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/config/postProcessing(/?.*)', name='config:postprocessing')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_postProcessing.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Post Processing'),
                        header=_('Post Processing'), topmenu='config',
                        controller="config", action="postProcessing")

    def savePostProcessing(self, kodi_data=None, kodi_12plus_data=None,
                           mediabrowser_data=None, sony_ps3_data=None,
                           wdtv_data=None, tivo_data=None, mede8er_data=None,
                           keep_processed_dir=None, process_method=None, processor_follow_symlinks=None,
                           del_rar_contents=None, process_automatically=None,
                           no_delete=None, rename_episodes=None, airdate_episodes=None,
                           file_timestamp_timezone=None,
                           unpack=None, unpack_dir=None, unrar_tool=None, alt_unrar_tool=None,
                           move_associated_files=None, delete_non_associated_files=None, sync_files=None,
                           postpone_if_sync_files=None,
                           allowed_extensions=None, tv_download_dir=None,
                           create_missing_show_dirs=None, add_shows_wo_dir=None,
                           extra_scripts=None, nfo_rename=None,
                           naming_pattern=None, naming_multi_ep=None,
                           naming_custom_abd=None, naming_anime=None,
                           naming_abd_pattern=None, naming_strip_year=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None,
                           naming_anime_multi_ep=None, autopostprocessor_frequency=None,
                           use_icacls=None):

        results = []

        if not config.change_tv_download_dir(tv_download_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, tv_download_dir) + ", dir not changed."]

        config.change_postprocessor_frequency(autopostprocessor_frequency)
        config.change_process_automatically(process_automatically)
        sickbeard.USE_ICACLS = config.checkbox_to_value(use_icacls)

        config.change_unrar_tool(unrar_tool, alt_unrar_tool)

        unpack = try_int(unpack)
        if unpack == sickbeard.UNPACK_PROCESS_CONTENTS:
            sickbeard.UNPACK = int(self.isRarSupported() != 'not supported')
            if sickbeard.UNPACK != sickbeard.UNPACK_PROCESS_CONTENTS:
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        elif unpack in sickbeard.unpackStrings:
            sickbeard.UNPACK = unpack

        if not config.change_unpack_dir(unpack_dir):
            results += ["Unable to change unpack directory to " + ek(os.path.normpath, unpack_dir) + ", check the logs."]

        sickbeard.NO_DELETE = config.checkbox_to_value(no_delete)
        sickbeard.KEEP_PROCESSED_DIR = config.checkbox_to_value(keep_processed_dir)
        sickbeard.CREATE_MISSING_SHOW_DIRS = config.checkbox_to_value(create_missing_show_dirs)
        sickbeard.ADD_SHOWS_WO_DIR = config.checkbox_to_value(add_shows_wo_dir)
        sickbeard.PROCESS_METHOD = process_method
        sickbeard.PROCESSOR_FOLLOW_SYMLINKS = config.checkbox_to_value(processor_follow_symlinks)
        sickbeard.DELRARCONTENTS = config.checkbox_to_value(del_rar_contents)
        sickbeard.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickbeard.RENAME_EPISODES = config.checkbox_to_value(rename_episodes)
        sickbeard.AIRDATE_EPISODES = config.checkbox_to_value(airdate_episodes)
        sickbeard.FILE_TIMESTAMP_TIMEZONE = file_timestamp_timezone
        sickbeard.MOVE_ASSOCIATED_FILES = config.checkbox_to_value(move_associated_files)
        sickbeard.DELETE_NON_ASSOCIATED_FILES = config.checkbox_to_value(delete_non_associated_files)
        sickbeard.SYNC_FILES = sync_files
        sickbeard.POSTPONE_IF_SYNC_FILES = config.checkbox_to_value(postpone_if_sync_files)

        sickbeard.ALLOWED_EXTENSIONS = ','.join({x.strip() for x in allowed_extensions.split(',') if x.strip()})
        sickbeard.NAMING_CUSTOM_ABD = config.checkbox_to_value(naming_custom_abd)
        sickbeard.NAMING_CUSTOM_SPORTS = config.checkbox_to_value(naming_custom_sports)
        sickbeard.NAMING_CUSTOM_ANIME = config.checkbox_to_value(naming_custom_anime)
        sickbeard.NAMING_STRIP_YEAR = config.checkbox_to_value(naming_strip_year)
        sickbeard.NFO_RENAME = config.checkbox_to_value(nfo_rename)

        sickbeard.METADATA_KODI = kodi_data
        sickbeard.METADATA_KODI_12PLUS = kodi_12plus_data
        sickbeard.METADATA_MEDIABROWSER = mediabrowser_data
        sickbeard.METADATA_PS3 = sony_ps3_data
        sickbeard.METADATA_WDTV = wdtv_data
        sickbeard.METADATA_TIVO = tivo_data
        sickbeard.METADATA_MEDE8ER = mede8er_data

        sickbeard.metadata_provider_dict['KODI'].set_config(sickbeard.METADATA_KODI)
        sickbeard.metadata_provider_dict['KODI 12+'].set_config(sickbeard.METADATA_KODI_12PLUS)
        sickbeard.metadata_provider_dict['MediaBrowser'].set_config(sickbeard.METADATA_MEDIABROWSER)
        sickbeard.metadata_provider_dict['Sony PS3'].set_config(sickbeard.METADATA_PS3)
        sickbeard.metadata_provider_dict['WDTV'].set_config(sickbeard.METADATA_WDTV)
        sickbeard.metadata_provider_dict['TIVO'].set_config(sickbeard.METADATA_TIVO)
        sickbeard.metadata_provider_dict['Mede8er'].set_config(sickbeard.METADATA_MEDE8ER)

        if self.isNamingValid(naming_pattern, naming_multi_ep, anime_type=naming_anime) != "invalid":
            sickbeard.NAMING_PATTERN = naming_pattern
            sickbeard.NAMING_MULTI_EP = try_int(naming_multi_ep, NAMING_LIMITED_EXTEND_E_PREFIXED)
            sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid normal naming config, not saving your naming settings"))

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickbeard.NAMING_ANIME_PATTERN = naming_anime_pattern
            sickbeard.NAMING_ANIME_MULTI_EP = try_int(naming_anime_multi_ep, NAMING_LIMITED_EXTEND_E_PREFIXED)
            sickbeard.NAMING_ANIME = try_int(naming_anime, 3)
            sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            sickbeard.NAMING_ABD_PATTERN = naming_abd_pattern
        else:
            results.append("You tried saving an invalid air-by-date naming config, not saving your air-by-date settings")

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            sickbeard.NAMING_SPORTS_PATTERN = naming_sports_pattern
        else:
            results.append("You tried saving an invalid sports naming config, not saving your sports settings")

        sickbeard.save_config()

        if results:
            for x in results:
                logger.log(x, logger.WARNING)
            ui.notifications.error(_('Error(s) Saving Configuration'), '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/postProcessing/")

    @staticmethod
    def testNaming(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        result = naming.test_name(pattern, try_int(multi, None), abd, sports, try_int(anime_type, None))
        result = ek(os.path.join, result[b'dir'], result[b'name'])

        return result

    @staticmethod
    def isNamingValid(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        if not pattern:
            return "invalid"

        # air by date shows just need one check, we don't need to worry about season folders
        if abd:
            is_valid = naming.check_valid_abd_naming(pattern)
            require_season_folders = False

        # sport shows just need one check, we don't need to worry about season folders
        elif sports:
            is_valid = naming.check_valid_sports_naming(pattern)
            require_season_folders = False

        else:
            # check validity of single and multi ep cases for the whole path
            is_valid = naming.check_valid_naming(pattern, try_int(multi, None), try_int(anime_type, None))

            # check validity of single and multi ep cases for only the file name
            require_season_folders = naming.check_force_season_folders(pattern, try_int(multi, None), try_int(anime_type, None))

        if is_valid and not require_season_folders:
            return "valid"
        elif is_valid and require_season_folders:
            return "seasonfolders"
        else:
            return "invalid"

    @staticmethod
    def isRarSupported():
        """
        Test Unpacking Support: - checks if unrar is installed and accesible
        """
        check = config.change_unrar_tool(sickbeard.UNRAR_TOOL, sickbeard.ALT_UNRAR_TOOL)
        if not check:
            logger.log('Looks like unrar is not installed, check failed', logger.WARNING)
        return ('not supported', 'supported')[check]
