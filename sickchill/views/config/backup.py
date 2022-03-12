from tornado.web import addslash

from sickchill import settings
from sickchill.oldbeard import helpers
from sickchill.update_manager import UpdateManager
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from .index import Config


@Route("/config/backuprestore(/?.*)", name="config:backup")
class ConfigBackupRestore(Config):
    def initialize(self):
        self.update_manager = UpdateManager()

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

    def backup(self, backup_dir=None):

        result = self.update_manager.backup(backup_dir)
        status = ("FAILED", "SUCCESSFUL")[bool(result)]
        return f"Backup to {backup_dir} {status}<br>\n"

    @staticmethod
    def restore(backupFile=None):

        finalResult = ""

        if backupFile:
            source = backupFile
            target_dir = settings.DATA_DIR / "restore"

            if helpers.restore_config_zip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickchill to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br>\n"

        return finalResult
