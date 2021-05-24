import os
import time

from tornado.web import addslash

from sickchill import settings
from sickchill.oldbeard import helpers
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from .index import Config


@Route("/config/backuprestore(/?.*)", name="config:backup")
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_backuprestore.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Backup/Restore"),
            header=_("Backup/Restore"),
            topmenu="config",
            controller="config",
            action="backupRestore",
        )

    @staticmethod
    def backup(backupDir=None):

        finalResult = ""

        if backupDir:
            source = [
                os.path.join(settings.DATA_DIR, "sickchill.db"),
                settings.CONFIG_FILE,
                os.path.join(settings.DATA_DIR, "failed.db"),
                os.path.join(settings.DATA_DIR, "cache.db"),
            ]
            target = os.path.join(backupDir, "sickchill-" + time.strftime("%Y%m%d%H%M%S") + ".zip")

            for (path, dirs, files) in os.walk(settings.CACHE_DIR, topdown=True):
                for dirname in dirs:
                    if path == settings.CACHE_DIR and dirname not in ["images"]:
                        dirs.remove(dirname)
                for filename in files:
                    source.append(os.path.join(path, filename))

            if helpers.backup_config_zip(source, target, settings.DATA_DIR):
                finalResult += "Successful backup to " + target
            else:
                finalResult += "Backup FAILED"
        else:
            finalResult += "You need to choose a folder to save your backup to!"

        finalResult += "<br>\n"

        return finalResult

    @staticmethod
    def restore(backupFile=None):

        finalResult = ""

        if backupFile:
            source = backupFile
            target_dir = os.path.join(settings.DATA_DIR, "restore")

            if helpers.restore_config_zip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickchill to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br>\n"

        return finalResult
