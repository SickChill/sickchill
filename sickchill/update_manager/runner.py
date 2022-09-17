import datetime
import glob
import os
import re
import time

from sickchill import logger, settings
from sickchill.helper.exceptions import UpdaterException
from sickchill.init_helpers import check_installed, git_folder, pyproject_file
from sickchill.oldbeard import db, helpers, ui

from .pip import PipUpdateManager


class UpdateManager(object):
    """
    Version check class meant to run as a thread object with the sc scheduler.
    """

    def __init__(self):
        self.updater = None
        self.install_type = None
        self.amActive = False

        self.install_type = self.find_install_type()
        if self.install_type == "git":
            self.updater = None
        elif self.install_type == "source":
            self.updater = None
        elif self.install_type == "pip":
            self.updater = PipUpdateManager()

        self.session = helpers.make_session()

    def run(self, force=False):

        self.amActive = True

        if self.updater:
            if self.check_for_new_version(force):
                if settings.AUTO_UPDATE:
                    logger.info("New update found for SickChill, starting auto-updater ...")
                    ui.notifications.message(_("New update found for SickChill, starting auto-updater"))
                    if self.run_backup_if_safe():
                        if settings.versionCheckScheduler.action.update():
                            logger.info("Update was successful!")
                            ui.notifications.message(_("Update was successful"))
                            settings.events.put(settings.events.SystemEvent.RESTART)
                        else:
                            logger.info("Update failed!")
                            ui.notifications.message(_("Update failed!"))

        self.check_for_new_news()

        self.amActive = False

    def run_backup_if_safe(self):
        return self.safe_to_update() is True and self._run_backup() is True

    def _run_backup(self):
        # Do a system backup before update
        logger.info("Config backup in progress...")
        ui.notifications.message(_("Backup"), _("Config backup in progress..."))
        try:
            backup_dir = os.path.join(settings.DATA_DIR, "backup")
            if not os.path.isdir(backup_dir):
                os.mkdir(backup_dir)

            if self._keep_latest_backup(backup_dir) and self._backup(backup_dir):
                logger.info("Config backup successful, updating...")
                ui.notifications.message(_("Backup"), _("Config backup successful, updating..."))
                return True
            else:
                logger.exception("Config backup failed, aborting update")
                ui.notifications.message(_("Backup"), _("Config backup failed, aborting update"))
                return False
        except Exception as error:
            logger.exception("Update: Config backup failed. Error: {}".format(error))
            ui.notifications.message(_("Backup"), _("Config backup failed, aborting update"))
            return False

    @staticmethod
    def _keep_latest_backup(backup_dir=None):
        if not backup_dir:
            return False

        files = glob.glob(os.path.join(glob.escape(backup_dir), "*.zip"))
        if not files:
            return True

        now = time.time()
        newest = files[0], now - os.path.getctime(files[0])
        for f in files[1:]:
            age = now - os.path.getctime(f)
            if age < newest[1]:
                newest = f, age
        files.remove(newest[0])

        for f in files:
            os.remove(f)

        return True

    @staticmethod
    def _backup(backup_dir=None):
        if not backup_dir:
            return False
        source = [
            os.path.join(settings.DATA_DIR, "sickchill.db"),
            settings.CONFIG_FILE,
            os.path.join(settings.DATA_DIR, "failed.db"),
            os.path.join(settings.DATA_DIR, "cache.db"),
        ]
        target = os.path.join(backup_dir, "sickchill-" + time.strftime("%Y%m%d%H%M%S") + ".zip")

        for (path, dirs, files) in os.walk(settings.CACHE_DIR):
            for dirname in dirs:
                if path == settings.CACHE_DIR and dirname not in ["images"]:
                    dirs.remove(dirname)
            for filename in files:
                source.append(os.path.join(path, filename))

        return helpers.backup_config_zip(source, target, settings.DATA_DIR)

    def safe_to_update(self):
        def db_safe():
            message = {
                "equal": {"type": logger.DEBUG, "text": "We can proceed with the update. New update has same DB version"},
                "upgrade": {"type": logger.WARNING, "text": "We can't proceed with the update. New update has a new DB version. Please manually update"},
                "downgrade": {
                    "type": logger.ERROR,
                    "text": "We can't proceed with the update. New update has a old DB version. It's not possible to downgrade",
                },
            }
            try:
                result = self.compare_db_version()
                if result in message:
                    logger.log(message[result]["type"], message[result]["text"])  # unpack the result message into a log entry
                else:
                    logger.warning("We can't proceed with the update. Unable to check remote DB version. Error: {0}".format(result))
                return result in ["equal"]  # add future True results to the list
            except Exception as error:
                logger.warning(f"We can't proceed with the update. Unable to compare DB version. Error: {error}")
                return False

        def postprocessor_safe():
            if not settings.autoPostProcessorScheduler.action.amActive:
                logger.debug("We can proceed with the update. Post-Processor is not running")
                return True
            else:
                logger.debug("We can't proceed with the update. Post-Processor is running")
                return False

        def showupdate_safe():
            if not settings.showUpdateScheduler.action.amActive:
                logger.debug("We can proceed with the update. Shows are not being updated")
                return True
            else:
                logger.debug("We can't proceed with the update. Shows are being updated")
                return False

        db_safe = db_safe()
        postprocessor_safe = postprocessor_safe()
        showupdate_safe = showupdate_safe()

        if db_safe and postprocessor_safe and showupdate_safe:
            logger.debug("Proceeding with auto update")
            return True
        else:
            logger.debug("Auto update aborted")
            return False

    def compare_db_version(self):
        try:
            self.need_update()
            newest_version = self.get_newest_version()
            response = helpers.getURL(
                f"https://raw.githubusercontent.com/{settings.GIT_ORG}/{settings.GIT_REPO}/{newest_version}/sickchill/oldbeard/databases/main.py",
                session=self.session,
                returns="text",
            )
            if not response:
                response = helpers.getURL(
                    f"https://raw.githubusercontent.com/{settings.GIT_ORG}/{settings.GIT_REPO}/master/sickchill/oldbeard/databases/main.py",
                    session=self.session,
                    returns="text",
                )

            if not response:
                raise UpdaterException(f"Empty response from GitHub for {newest_version}")

            match = re.search(r"MAX_DB_VERSION\s=\s(?P<version>\d{2,3})", response)
            destination_db_version = int(match.group("version"))
            main_db_con = db.DBConnection()
            current_db_version = main_db_con.get_db_version()
            if destination_db_version > current_db_version:
                return "upgrade"
            elif destination_db_version == current_db_version:
                return "equal"
            else:
                return "downgrade"
        except Exception as error:
            return f"{error}"

    @staticmethod
    def find_install_type():
        """
        Determines how this copy of sc was installed.

        returns: type of installation. Possible values are:
            'win': any compiled windows build
            'git': running from source using git
            'source': running from source without git
        """

        if git_folder.is_dir():
            install_type = "git"
        elif pyproject_file.is_file():
            install_type = "source"
        elif check_installed():
            install_type = "pip"

        return install_type

    def check_for_new_version(self, force=False):
        """
        Checks the internet for a newer version.

        returns: bool, True for new version or False for no new version.

        force: if true the VERSION_NOTIFY setting will be ignored and a check will be forced
        """

        if self.install_type != "pip":
            logger.info("We no longer support updating from source, please use git or pip")
            return False

        if not self.updater or (not settings.VERSION_NOTIFY and not settings.AUTO_UPDATE and not force):
            logger.info("Version checking is disabled, not checking for the newest version")
            return False

        # checking for updates
        if not settings.AUTO_UPDATE:
            logger.info("Checking for updates using " + self.install_type.upper())

        if not self.need_update():
            if force:
                ui.notifications.message(_("No update needed"))
                logger.info("No update needed")

            # no updates needed
            return False

        # found updates
        self.set_newest_text()
        return True

    def check_for_new_news(self):
        """
        Checks GitHub for the latest news.

        returns: str, a copy of the news

        force: ignored
        """

        # Grab a copy of the news
        logger.debug("check_for_new_news: Checking GitHub for latest news.")
        try:
            news = helpers.getURL(settings.NEWS_URL, session=self.session, returns="text")
        except Exception:
            logger.warning("check_for_new_news: Could not load news from repo.")
            news = ""

        if not news:
            return ""

        try:
            last_read = datetime.datetime.strptime(settings.NEWS_LAST_READ, "%Y-%m-%d")
        except Exception:
            last_read = 0

        settings.NEWS_UNREAD = 0
        found_news = False
        for match in re.finditer(r"^####\s*(\d{4}-\d{2}-\d{2})\s*####", news, re.M):
            if not found_news:
                found_news = True
                settings.NEWS_LATEST = match.group(1)

            try:
                if datetime.datetime.strptime(match.group(1), "%Y-%m-%d") > last_read:
                    settings.NEWS_UNREAD += 1
            except Exception:
                pass

        return news

    def update(self):
        if self.need_update():
            return self.updater.update()

    def need_update(self):
        if self.updater:
            return self.updater.need_update()

    def backup(self):
        if self.updater:
            return self._run_backup

    def get_newest_version(self):
        if self.updater:
            return self.updater.get_newest_version()

    def get_current_version(self):
        if self.updater:
            return self.updater.get_current_version()

    def get_version_delta(self):
        if self.updater:
            return self.updater.get_version_delta()

    def set_newest_text(self):
        if self.updater:
            return self.updater.set_newest_text()
