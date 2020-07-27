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
# Stdlib Imports
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickchill.start
from sickbeard import config, filters, ui
from sickchill import settings
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from .index import Config


@Route('/config/anime(/?.*)', name='config:anime')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):

        t = PageTemplate(rh=self, filename="config_anime.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Anime'),
                        header=_('Anime'), topmenu='config',
                        controller="config", action="anime")

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None, split_home_in_tabs=None):

        settings.USE_ANIDB = config.checkbox_to_value(use_anidb)
        settings.ANIDB_USERNAME = anidb_username
        settings.ANIDB_PASSWORD = filters.unhide(settings.ANIDB_PASSWORD, anidb_password)
        settings.ANIDB_USE_MYLIST = config.checkbox_to_value(anidb_use_mylist)
        settings.ANIME_SPLIT_HOME = config.checkbox_to_value(split_home)
        settings.ANIME_SPLIT_HOME_IN_TABS = config.checkbox_to_value(split_home_in_tabs)

        sickchill.start.save_config()
        ui.notifications.message(_('Configuration Saved'), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/anime/")
