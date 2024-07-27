import os

from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.oldbeard import config, filters, subtitles as subtitle_module, ui
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/subtitles(/?.*)", name="config:subtitles")
class ConfigSubtitles(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_subtitles.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Subtitles"),
            header=_("Subtitles"),
            topmenu="config",
            controller="config",
            action="subtitles",
        )

    def saveSubtitles(self):
        config.change_subtitle_finder_frequency(self.get_body_argument("subtitles_finder_frequency", default=None))
        config.change_use_subtitles(self.get_body_argument("use_subtitles", default=None))

        subtitles_languages = self.get_body_argument("subtitles_languages", default=None)
        settings.SUBTITLES_INCLUDE_SPECIALS = config.checkbox_to_value(self.get_body_argument("subtitles_include_specials", default=None))
        settings.SUBTITLES_LANGUAGES = (
            [code.strip() for code in subtitles_languages.split(",") if code.strip() in subtitle_module.subtitle_code_filter()] if subtitles_languages else []
        )

        subtitles_extra_scripts = self.get_body_argument("subtitles_extra_scripts", default=None)
        settings.SUBTITLES_DIR = self.get_body_argument("subtitles_dir", default=None)
        settings.SUBTITLES_PERFECT_MATCH = config.checkbox_to_value(self.get_body_argument("subtitles_perfect_match", default=None))
        settings.SUBTITLES_HISTORY = config.checkbox_to_value(self.get_body_argument("subtitles_history", default=None))
        settings.EMBEDDED_SUBTITLES_ALL = config.checkbox_to_value(self.get_body_argument("embedded_subtitles_all", default=None))
        settings.SUBTITLES_HEARING_IMPAIRED = config.checkbox_to_value(self.get_body_argument("subtitles_hearing_impaired", default=None))
        settings.SUBTITLES_MULTI = config.checkbox_to_value(self.get_body_argument("subtitles_multi", default=None))
        settings.SUBTITLES_KEEP_ONLY_WANTED = config.checkbox_to_value(self.get_body_argument("subtitles_keep_only_wanted", default=None))
        settings.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split("|") if x.strip()]

        # Subtitles services
        services_str_list = self.get_body_argument("service_order", default=None).split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for cur_service_str in services_str_list:
            cur_service, cur_enabled = cur_service_str.split(":")
            subtitles_services_list.append(cur_service)
            subtitles_services_enabled.append(int(cur_enabled))

        settings.SUBTITLES_SERVICES_LIST = subtitles_services_list
        settings.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        settings.ADDIC7ED_USER = self.get_body_argument("addic7ed_user", default="")
        settings.ADDIC7ED_PASS = filters.unhide(settings.ADDIC7ED_PASS, self.get_body_argument("addic7ed_pass", default=""))
        settings.ITASA_USER = self.get_body_argument("itasa_user", default="")
        settings.ITASA_PASS = filters.unhide(settings.ITASA_PASS, self.get_body_argument("itasa_pass", default="")) or ""
        settings.OPENSUBTITLES_USER = self.get_body_argument("opensubtitles_user", default="")
        settings.OPENSUBTITLES_PASS = filters.unhide(settings.OPENSUBTITLES_PASS, self.get_body_argument("opensubtitles_pass", default=""))
        settings.SUBSCENTER_USER = self.get_body_argument("subscenter_user", default="")
        settings.SUBSCENTER_PASS = filters.unhide(settings.SUBSCENTER_PASS, self.get_body_argument("subscenter_pass", default=""))

        sickchill.start.save_config()
        # Reset provider pool so next time we use the newest settings
        subtitle_module.SubtitleProviderPool().reset()

        ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/subtitles/")
