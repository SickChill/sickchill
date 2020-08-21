import os
import subprocess

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    def notify_snatch(self, ep_name):
        if settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH:
            self._send_synologyNotifier(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD:
            self._send_synologyNotifier(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._send_synologyNotifier(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if settings.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._send_synologyNotifier(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if settings.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_synologyNotifier(update_text.format(ipaddress), title)

    @staticmethod
    def _send_synologyNotifier(message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        logger.info("Executing command " + str(synodsmnotify_cmd))
        logger.debug("Absolute path to command: " + os.path.abspath(synodsmnotify_cmd[0]))
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=settings.DATA_DIR, universal_newlines=True)
            out, err = p.communicate()
            logger.debug(_("Script result: {0}").format(str(out or err).strip()))
        except OSError as e:
            logger.info("Unable to run synodsmnotify: " + str(e))
