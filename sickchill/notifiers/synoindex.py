import os
import subprocess

from sickchill import logger, settings


class Notifier(object):
    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_update(self, new_version):
        pass

    def notify_login(self, ipaddress=""):
        pass

    def moveFolder(self, old_path, new_path):
        self.moveObject(old_path, new_path)

    def moveFile(self, old_file, new_file):
        self.moveObject(old_file, new_file)

    @staticmethod
    def moveObject(old_path, new_path):
        if settings.USE_SYNOINDEX:
            synoindex_cmd = ["/usr/syno/bin/synoindex", "-N", os.path.abspath(new_path), os.path.abspath(old_path)]
            logger.debug(f"Executing command {synoindex_cmd}")
            logger.debug(f"Absolute path to command: {os.path.abspath(synoindex_cmd[0])}")
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=settings.DATA_DIR, universal_newlines=True)
                out, err = p.communicate()
                logger.debug(_("Script result: {0}").format(str(out or err).strip()))
            except OSError as error:
                logger.exception(f"Unable to run synoindex: {error}")

    def deleteFolder(self, cur_path):
        self.makeObject("-D", cur_path)

    def addFolder(self, cur_path):
        self.makeObject("-A", cur_path)

    def deleteFile(self, cur_file):
        self.makeObject("-d", cur_file)

    def addFile(self, cur_file):
        self.makeObject("-a", cur_file)

    @staticmethod
    def makeObject(cmd_arg, cur_path):
        if settings.USE_SYNOINDEX:
            synoindex_cmd = ["/usr/syno/bin/synoindex", cmd_arg, os.path.abspath(cur_path)]
            logger.debug(f"Executing command {synoindex_cmd}")
            logger.debug("Absolute path to command: " + os.path.abspath(synoindex_cmd[0]))
            try:
                p = subprocess.Popen(synoindex_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=settings.DATA_DIR, universal_newlines=True)
                out, err = p.communicate()
                logger.debug(_("Script result: {0}").format(str(out or err).strip()))
            except OSError as error:
                logger.exception(f"Unable to run synoindex: {error}")
