import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, naming, ui
from sickchill.oldbeard.common import NAMING_LIMITED_EXTEND_E_PREFIXED
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/postProcessing(/?.*)", name="config:postprocessing")
class ConfigPostProcessing(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_postProcessing.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Post Processing"),
            header=_("Post Processing"),
            topmenu="config",
            controller="config",
            action="postProcessing",
        )

    def savePostProcessing(self):
        tv_download_dir = self.get_body_argument("tv_download_dir", default=None)
        results = []

        if not config.change_tv_download_dir(tv_download_dir):
            results += ["Unable to create directory " + os.path.normpath(tv_download_dir) + ", dir not changed."]

        config.change_postprocessor_frequency(self.get_body_argument("autopostprocessor_frequency", default=None))
        config.change_process_automatically(self.get_body_argument("process_automatically", default=None))
        settings.USE_ICACLS = config.checkbox_to_value(self.get_body_argument("use_icacls", default=None))

        config.change_unrar_tool(self.get_body_argument("unrar_tool", default=None), self.get_body_argument("unar_tool", default=None))

        unpack = try_int(self.get_body_argument("unpack", default=None))
        if unpack == settings.UNPACK_PROCESS_CONTENTS:
            settings.UNPACK = int(self.isRarSupported() != "not supported")
            if settings.UNPACK != settings.UNPACK_PROCESS_CONTENTS:
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        elif unpack in settings.unpackStrings:
            settings.UNPACK = unpack

        unpack_dir = self.get_body_argument("unpack_dir", default=None)
        if not config.change_unpack_dir(unpack_dir):
            results += ["Unable to change unpack directory to " + os.path.normpath(unpack_dir) + ", check the logs."]

        settings.NO_DELETE = config.checkbox_to_value(self.get_body_argument("no_delete", default=None))
        settings.KEEP_PROCESSED_DIR = config.checkbox_to_value(self.get_body_argument("keep_processed_dir", default=None))
        settings.CREATE_MISSING_SHOW_DIRS = config.checkbox_to_value(self.get_body_argument("create_missing_show_dirs", default=None))
        settings.ADD_SHOWS_WO_DIR = config.checkbox_to_value(self.get_body_argument("add_shows_wo_dir", default=None))
        settings.PROCESS_METHOD = self.get_body_argument("process_method", default=None)
        settings.PROCESSOR_FOLLOW_SYMLINKS = config.checkbox_to_value(self.get_body_argument("processor_follow_symlinks", default=None))
        settings.DELRARCONTENTS = config.checkbox_to_value(self.get_body_argument("del_rar_contents", default=None))
        extra_scripts = self.get_body_argument("extra_scripts", default=None)
        settings.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split("|") if x.strip()]
        settings.RENAME_EPISODES = config.checkbox_to_value(self.get_body_argument("rename_episodes", default=None))
        settings.AIRDATE_EPISODES = config.checkbox_to_value(self.get_body_argument("airdate_episodes", default=None))
        settings.FILE_TIMESTAMP_TIMEZONE = self.get_body_argument("file_timestamp_timezone", default=None)
        settings.MOVE_ASSOCIATED_FILES = config.checkbox_to_value(self.get_body_argument("move_associated_files", default=None))
        settings.DELETE_NON_ASSOCIATED_FILES = config.checkbox_to_value(self.get_body_argument("delete_non_associated_files", default=None))
        settings.SYNC_FILES = self.get_body_argument("sync_files", default=None)
        settings.POSTPONE_IF_SYNC_FILES = config.checkbox_to_value(self.get_body_argument("postpone_if_sync_files", default=None))

        allowed_extensions = self.get_body_argument("allowed_extensions", default=None)
        settings.ALLOWED_EXTENSIONS = ",".join({x.strip() for x in allowed_extensions.split(",") if x.strip()})
        settings.NAMING_CUSTOM_ABD = config.checkbox_to_value(self.get_body_argument("naming_custom_abd", default=None))
        settings.NAMING_CUSTOM_SPORTS = config.checkbox_to_value(self.get_body_argument("naming_custom_sports", default=None))
        settings.NAMING_CUSTOM_ANIME = config.checkbox_to_value(self.get_body_argument("naming_custom_anime", default=None))
        settings.NAMING_STRIP_YEAR = config.checkbox_to_value(self.get_body_argument("naming_strip_year", default=None))
        settings.NAMING_NO_BRACKETS = config.checkbox_to_value(self.get_body_argument("naming_no_brackets", default=None))
        settings.NFO_RENAME = config.checkbox_to_value(self.get_body_argument("nfo_rename", default=None))

        settings.METADATA_KODI = self.get_body_argument("kodi_data", default=None)
        settings.METADATA_MEDIABROWSER = self.get_body_argument("mediabrowser_data", default=None)
        settings.METADATA_PS3 = self.get_body_argument("sony_ps3_data", default=None)
        settings.METADATA_WDTV = self.get_body_argument("wdtv_data", default=None)
        settings.METADATA_TIVO = self.get_body_argument("tivo_data", default=None)
        settings.METADATA_MEDE8ER = self.get_body_argument("mede8er_data", default=None)

        settings.metadata_provider_dict["KODI"].set_config(settings.METADATA_KODI)
        settings.metadata_provider_dict["MediaBrowser"].set_config(settings.METADATA_MEDIABROWSER)
        settings.metadata_provider_dict["Sony PS3"].set_config(settings.METADATA_PS3)
        settings.metadata_provider_dict["WDTV"].set_config(settings.METADATA_WDTV)
        settings.metadata_provider_dict["TIVO"].set_config(settings.METADATA_TIVO)
        settings.metadata_provider_dict["Mede8er"].set_config(settings.METADATA_MEDE8ER)

        naming_pattern = self.get_body_argument("naming_pattern", default=None)
        naming_multi_ep = self.get_body_argument("naming_multi_ep", default=None)
        if self.isNamingValid(naming_pattern, naming_multi_ep) != "invalid":
            settings.NAMING_PATTERN = naming_pattern
            settings.NAMING_MULTI_EP = try_int(naming_multi_ep, NAMING_LIMITED_EXTEND_E_PREFIXED)
            settings.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid normal naming config, not saving your naming settings"))

        naming_anime_pattern = self.get_body_argument("naming_anime_pattern", default=None)
        naming_anime = self.get_body_argument("naming_anime", default=None)
        naming_anime_multi_ep = self.get_body_argument("naming_anime_multi_ep", default=None)
        naming_abd_pattern = self.get_body_argument("naming_abd_pattern", default=None)
        naming_sports_pattern = self.get_body_argument("naming_sports_pattern", default=None)
        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            settings.NAMING_ANIME_PATTERN = naming_anime_pattern
            settings.NAMING_ANIME_MULTI_EP = try_int(naming_anime_multi_ep, NAMING_LIMITED_EXTEND_E_PREFIXED)
            settings.NAMING_ANIME = try_int(naming_anime, 3)
            settings.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            settings.NAMING_ABD_PATTERN = naming_abd_pattern
        else:
            results.append("You tried saving an invalid air-by-date naming config, not saving your air-by-date settings")

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            settings.NAMING_SPORTS_PATTERN = naming_sports_pattern
        else:
            results.append("You tried saving an invalid sports naming config, not saving your sports settings")

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.warning(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/postProcessing/")

    @staticmethod
    def testNaming(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        result = naming.test_name(pattern, try_int(multi, None), abd, sports, try_int(anime_type, None))
        result = os.path.join(result["dir"], result["name"])

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
        Test Unpacking Support: - checks if unrar is installed and accessible
        """
        check = config.change_unrar_tool(settings.UNRAR_TOOL, settings.UNAR_TOOL)
        if not check:
            logger.warning("Looks like unrar is not installed, check failed")
        return ("not supported", "supported")[check]
