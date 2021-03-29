import os

from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.oldbeard import config, filters, subtitles as subtitle_module, ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/subtitles(/?.*)", name="config:subtitles")
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_subtitles.mako")

        return t.render(
            submenu=self.ConfigMenu(), title=_("Config - Subtitles"), header=_("Subtitles"), topmenu="config", controller="config", action="subtitles"
        )

    def saveSubtitles(
        self,
        use_subtitles=None,
        subtitles_include_specials=None,
        subtitles_languages=None,
        subtitles_dir=None,
        subtitles_perfect_match=None,
        service_order=None,
        subtitles_history=None,
        subtitles_finder_frequency=None,
        subtitles_multi=None,
        embedded_subtitles_all=None,
        subtitles_extra_scripts=None,
        subtitles_hearing_impaired=None,
        addic7ed_user=None,
        addic7ed_pass=None,
        itasa_user=None,
        itasa_pass=None,
        legendastv_user=None,
        legendastv_pass=None,
        opensubtitles_user=None,
        opensubtitles_pass=None,
        subscenter_user=None,
        subscenter_pass=None,
        subtitles_keep_only_wanted=None,
    ):

        config.change_subtitle_finder_frequency(subtitles_finder_frequency)
        config.change_use_subtitles(use_subtitles)

        settings.SUBTITLES_INCLUDE_SPECIALS = config.checkbox_to_value(subtitles_include_specials)
        settings.SUBTITLES_LANGUAGES = (
            [code.strip() for code in subtitles_languages.split(",") if code.strip() in subtitle_module.subtitle_code_filter()] if subtitles_languages else []
        )

        settings.SUBTITLES_DIR = subtitles_dir
        settings.SUBTITLES_PERFECT_MATCH = config.checkbox_to_value(subtitles_perfect_match)
        settings.SUBTITLES_HISTORY = config.checkbox_to_value(subtitles_history)
        settings.EMBEDDED_SUBTITLES_ALL = config.checkbox_to_value(embedded_subtitles_all)
        settings.SUBTITLES_HEARING_IMPAIRED = config.checkbox_to_value(subtitles_hearing_impaired)
        settings.SUBTITLES_MULTI = config.checkbox_to_value(subtitles_multi)
        settings.SUBTITLES_KEEP_ONLY_WANTED = config.checkbox_to_value(subtitles_keep_only_wanted)
        settings.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split("|") if x.strip()]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(":")
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        settings.SUBTITLES_SERVICES_LIST = subtitles_services_list
        settings.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        settings.ADDIC7ED_USER = addic7ed_user or ""
        settings.ADDIC7ED_PASS = filters.unhide(settings.ADDIC7ED_PASS, addic7ed_pass) or ""
        settings.ITASA_USER = itasa_user or ""
        settings.ITASA_PASS = filters.unhide(settings.ITASA_PASS, itasa_pass) or ""
        settings.LEGENDASTV_USER = legendastv_user or ""
        settings.LEGENDASTV_PASS = filters.unhide(settings.LEGENDASTV_PASS, legendastv_pass) or ""
        settings.OPENSUBTITLES_USER = opensubtitles_user or ""
        settings.OPENSUBTITLES_PASS = filters.unhide(settings.OPENSUBTITLES_PASS, opensubtitles_pass) or ""
        settings.SUBSCENTER_USER = subscenter_user or ""
        settings.SUBSCENTER_PASS = filters.unhide(settings.SUBSCENTER_PASS, subscenter_pass) or ""

        sickchill.start.save_config()
        # Reset provider pool so next time we use the newest settings
        subtitle_module.SubtitleProviderPool().reset()

        ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/subtitles/")
