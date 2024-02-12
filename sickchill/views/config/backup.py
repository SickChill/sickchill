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
    @addslash
    def index(self):
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
        final_result = ""

        if backupDir:
            source = [
                os.path.join(settings.DATA_DIR, "sickchill.db"),
                settings.CONFIG_FILE,
                os.path.join(settings.DATA_DIR, "failed.db"),
                os.path.join(settings.DATA_DIR, "cache.db"),
            ]
            target = os.path.join(backupDir, "sickchill-" + time.strftime("%Y%m%d%H%M%S") + ".zip")

            for path, dirs, files in os.walk(settings.CACHE_DIR, topdown=True):
                for dirname in dirs:
                    if path == settings.CACHE_DIR and dirname not in ["images"]:
                        dirs.remove(dirname)
                for filename in files:
                    source.append(os.path.join(path, filename))

            if helpers.backup_config_zip(source, target, settings.DATA_DIR):
                final_result += "Successful backup to " + target
            else:
                final_result += "Backup FAILED"
        else:
            final_result += "You need to choose a folder to save your backup to!"

        final_result += "<br>\n"

        return final_result

    @staticmethod
    def restore(backupFile=None):
        final_result = ""

        if backupFile:
            source = backupFile
            target_dir = os.path.join(settings.DATA_DIR, "restore")

            if helpers.restore_config_zip(source, target_dir):
                final_result += "Successfully extracted restore files to " + target_dir
                final_result += "<br>Restart sickchill to complete the restore."
            else:
                final_result += "Restore FAILED"
        else:
            final_result += "You need to select a backup file to restore!"

        final_result += "<br>\n"

        return final_result
