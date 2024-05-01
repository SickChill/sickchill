import os

from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.oldbeard import config, filters, ui
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/anime(/?.*)", name="config:anime")
class ConfigAnime(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_anime.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Anime"),
            header=_("Anime"),
            topmenu="config",
            controller="config",
            action="anime",
        )

    def saveAnime(self):
        settings.USE_ANIDB = config.checkbox_to_value(self.get_body_argument("use_anidb", default=None))
        settings.ANIDB_USERNAME = self.get_body_argument("anidb_username", default=None)
        settings.ANIDB_PASSWORD = filters.unhide(settings.ANIDB_PASSWORD, self.get_body_argument("anidb_password", default=None))
        settings.ANIDB_USE_MYLIST = config.checkbox_to_value(self.get_body_argument("anidb_use_mylist", default=None))
        settings.ANIME_SPLIT_HOME = config.checkbox_to_value(self.get_body_argument("split_home", default=None))
        settings.ANIME_SPLIT_HOME_IN_TABS = config.checkbox_to_value(self.get_body_argument("split_home_in_tabs", default=None))

        sickchill.start.save_config()
        ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/anime/")
