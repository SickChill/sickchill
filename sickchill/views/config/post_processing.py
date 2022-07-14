import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, naming, ui
from sickchill.oldbeard.common import NAMING_LIMITED_EXTEND_E_PREFIXED
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/postProcessing(/?.*)", name="config:postprocessing")
class ConfigPostProcessing(Config):
    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_postProcessing.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Post Processing"),
            header=_("Post Processing"),
            topmenu="config",
            controller="config",
            action="postProcessing",
        )

    def savePostProcessing(
        self,
        kodi_data=None,
        mediabrowser_data=None,
        sony_ps3_data=None,
        wdtv_data=None,
        tivo_data=None,
        mede8er_data=None,
        keep_processed_dir=None,
        process_method=None,
        processor_follow_symlinks=None,
        del_rar_contents=None,
        process_automatically=None,
        no_delete=None,
        rename_episodes=None,
        airdate_episodes=None,
        file_timestamp_timezone=None,
        unpack=None,
        unpack_dir=None,
        unrar_tool=None,
        unar_tool=None,
        move_associated_files=None,
        delete_non_associated_files=None,
        sync_files=None,
        postpone_if_sync_files=None,
        allowed_extensions=None,
        tv_download_dir=None,
        create_missing_show_dirs=None,
        add_shows_wo_dir=None,
        extra_scripts=None,
        nfo_rename=None,
        naming_pattern=None,
        naming_multi_ep=None,
        naming_custom_abd=None,
        naming_anime=None,
        naming_abd_pattern=None,
        naming_strip_year=None,
        naming_no_brackets=None,
        naming_custom_sports=None,
        naming_sports_pattern=None,
        naming_custom_anime=None,
        naming_anime_pattern=None,
        naming_anime_multi_ep=None,
        autopostprocessor_frequency=None,
        use_icacls=None,
    ):

        results = []

        if not config.change_tv_download_dir(tv_download_dir):
            results += ["Unable to create directory " + os.path.normpath(tv_download_dir) + ", dir not changed."]

        config.change_postprocessor_frequency(autopostprocessor_frequency)
        config.change_process_automatically(process_automatically)
        settings.USE_ICACLS = config.checkbox_to_value(use_icacls)

        config.change_unrar_tool(unrar_tool, unar_tool)

        unpack = try_int(unpack)
        if unpack == settings.UNPACK_PROCESS_CONTENTS:
            settings.UNPACK = int(self.isRarSupported() != "not supported")
            if settings.UNPACK != settings.UNPACK_PROCESS_CONTENTS:
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
        elif unpack in settings.unpackStrings:
            settings.UNPACK = unpack

        if not config.change_unpack_dir(unpack_dir):
            results += ["Unable to change unpack directory to " + os.path.normpath(unpack_dir) + ", check the logs."]

        settings.NO_DELETE = config.checkbox_to_value(no_delete)
        settings.KEEP_PROCESSED_DIR = config.checkbox_to_value(keep_processed_dir)
        settings.CREATE_MISSING_SHOW_DIRS = config.checkbox_to_value(create_missing_show_dirs)
        settings.ADD_SHOWS_WO_DIR = config.checkbox_to_value(add_shows_wo_dir)
        settings.PROCESS_METHOD = process_method
        settings.PROCESSOR_FOLLOW_SYMLINKS = config.checkbox_to_value(processor_follow_symlinks)
        settings.DELRARCONTENTS = config.checkbox_to_value(del_rar_contents)
        settings.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split("|") if x.strip()]
        settings.RENAME_EPISODES = config.checkbox_to_value(rename_episodes)
        settings.AIRDATE_EPISODES = config.checkbox_to_value(airdate_episodes)
        settings.FILE_TIMESTAMP_TIMEZONE = file_timestamp_timezone
        settings.MOVE_ASSOCIATED_FILES = config.checkbox_to_value(move_associated_files)
        settings.DELETE_NON_ASSOCIATED_FILES = config.checkbox_to_value(delete_non_associated_files)
        settings.SYNC_FILES = sync_files
        settings.POSTPONE_IF_SYNC_FILES = config.checkbox_to_value(postpone_if_sync_files)

        settings.ALLOWED_EXTENSIONS = ",".join({x.strip() for x in allowed_extensions.split(",") if x.strip()})
        settings.NAMING_CUSTOM_ABD = config.checkbox_to_value(naming_custom_abd)
        settings.NAMING_CUSTOM_SPORTS = config.checkbox_to_value(naming_custom_sports)
        settings.NAMING_CUSTOM_ANIME = config.checkbox_to_value(naming_custom_anime)
        settings.NAMING_STRIP_YEAR = config.checkbox_to_value(naming_strip_year)
        settings.NAMING_NO_BRACKETS = config.checkbox_to_value(naming_no_brackets)
        settings.NFO_RENAME = config.checkbox_to_value(nfo_rename)

        settings.METADATA_KODI = kodi_data
        settings.METADATA_MEDIABROWSER = mediabrowser_data
        settings.METADATA_PS3 = sony_ps3_data
        settings.METADATA_WDTV = wdtv_data
        settings.METADATA_TIVO = tivo_data
        settings.METADATA_MEDE8ER = mede8er_data

        settings.metadata_provider_dict["KODI"].set_config(settings.METADATA_KODI)
        settings.metadata_provider_dict["MediaBrowser"].set_config(settings.METADATA_MEDIABROWSER)
        settings.metadata_provider_dict["Sony PS3"].set_config(settings.METADATA_PS3)
        settings.metadata_provider_dict["WDTV"].set_config(settings.METADATA_WDTV)
        settings.metadata_provider_dict["TIVO"].set_config(settings.METADATA_TIVO)
        settings.metadata_provider_dict["Mede8er"].set_config(settings.METADATA_MEDE8ER)

        if self.isNamingValid(naming_pattern, naming_multi_ep) != "invalid":
            settings.NAMING_PATTERN = naming_pattern
            settings.NAMING_MULTI_EP = try_int(naming_multi_ep, NAMING_LIMITED_EXTEND_E_PREFIXED)
            settings.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            results.append(_("You tried saving an invalid normal naming config, not saving your naming settings"))

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
        Test Unpacking Support: - checks if unrar is installed and accesible
        """
        check = config.change_unrar_tool(settings.UNRAR_TOOL, settings.UNAR_TOOL)
        if not check:
            logger.warning("Looks like unrar is not installed, check failed")
        return ("not supported", "supported")[check]
