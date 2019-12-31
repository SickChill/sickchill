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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import config, filters, subtitles as subtitle_module, ui
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from . import Config

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/config/subtitles(/?.*)', name='config:subtitles')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_subtitles.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Subtitles'),
                        header=_('Subtitles'), topmenu='config',
                        controller="config", action="subtitles")

    def saveSubtitles(
            self, use_subtitles=None, subtitles_include_specials=None, subtitles_plugins=None, subtitles_languages=None, subtitles_dir=None,
            subtitles_perfect_match=None, service_order=None, subtitles_history=None, subtitles_finder_frequency=None, subtitles_multi=None,
            embedded_subtitles_all=None, subtitles_extra_scripts=None, subtitles_hearing_impaired=None, addic7ed_user=None, addic7ed_pass=None, itasa_user=None,
            itasa_pass=None, legendastv_user=None, legendastv_pass=None, opensubtitles_user=None, opensubtitles_pass=None, subscenter_user=None,
            subscenter_pass=None, subtitles_download_in_pp=None, subtitles_keep_only_wanted=None):

        config.change_subtitle_finder_frequency(subtitles_finder_frequency)
        config.change_use_subtitles(use_subtitles)

        sickbeard.SUBTITLES_INCLUDE_SPECIALS = config.checkbox_to_value(subtitles_include_specials)
        sickbeard.SUBTITLES_LANGUAGES = [
            code.strip() for code in subtitles_languages.split(',') if code.strip() in subtitle_module.subtitle_code_filter()
        ] if subtitles_languages else []

        sickbeard.SUBTITLES_DIR = subtitles_dir
        sickbeard.SUBTITLES_PERFECT_MATCH = config.checkbox_to_value(subtitles_perfect_match)
        sickbeard.SUBTITLES_HISTORY = config.checkbox_to_value(subtitles_history)
        sickbeard.EMBEDDED_SUBTITLES_ALL = config.checkbox_to_value(embedded_subtitles_all)
        sickbeard.SUBTITLES_HEARING_IMPAIRED = config.checkbox_to_value(subtitles_hearing_impaired)
        sickbeard.SUBTITLES_MULTI = config.checkbox_to_value(subtitles_multi)
        sickbeard.SUBTITLES_DOWNLOAD_IN_PP = config.checkbox_to_value(subtitles_download_in_pp)
        sickbeard.SUBTITLES_KEEP_ONLY_WANTED = config.checkbox_to_value(subtitles_keep_only_wanted)
        sickbeard.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split('|') if x.strip()]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(':')
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        sickbeard.SUBTITLES_SERVICES_LIST = subtitles_services_list
        sickbeard.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        sickbeard.ADDIC7ED_USER = addic7ed_user or ''
        sickbeard.ADDIC7ED_PASS = filters.unhide(sickbeard.ADDIC7ED_PASS, addic7ed_pass) or ''
        sickbeard.ITASA_USER = itasa_user or ''
        sickbeard.ITASA_PASS = filters.unhide(sickbeard.ITASA_PASS, itasa_pass) or ''
        sickbeard.LEGENDASTV_USER = legendastv_user or ''
        sickbeard.LEGENDASTV_PASS = filters.unhide(sickbeard.LEGENDASTV_PASS, legendastv_pass) or ''
        sickbeard.OPENSUBTITLES_USER = opensubtitles_user or ''
        sickbeard.OPENSUBTITLES_PASS = filters.unhide(sickbeard.OPENSUBTITLES_PASS, opensubtitles_pass) or ''
        sickbeard.SUBSCENTER_USER = subscenter_user or ''
        sickbeard.SUBSCENTER_PASS = filters.unhide(sickbeard.SUBSCENTER_PASS, subscenter_pass) or ''

        sickbeard.save_config()
        # Reset provider pool so next time we use the newest settings
        subtitle_module.SubtitleProviderPool().reset()

        ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/subtitles/")
