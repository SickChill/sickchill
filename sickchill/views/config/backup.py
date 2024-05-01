import os

from tornado.web import addslash

import sickchill.update_manager
from sickchill import settings
from sickchill.oldbeard import helpers
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


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

    def backup(self):
        backup_dir = self.get_body_argument("backupDirectory", default="")
        final_result = ""

        if backup_dir:
            updater = sickchill.update_manager.UpdateManager()
            target = updater.backup_to_dir(backup_dir)
            if target:
                final_result += f"Successful backup to {target}"
            else:
                final_result += "Backup FAILED"
        else:
            final_result += "You need to choose a folder to save your backup to!"

        final_result += "<br>\n"

        return final_result

    def restore(self):
        backup_file = self.get_body_argument("backupFile", default="")

        final_result = ""

        if backup_file:
            source = backup_file
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
