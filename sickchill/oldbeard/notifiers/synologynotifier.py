import os
import subprocess

from sickchill import logger, settings
from sickchill.oldbeard import common
from sickchill.oldbeard.classes import UIError


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

    def notify_update(self, new_version="??"):
        if settings.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            self._send_synologyNotifier(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if settings.USE_SYNOLOGYNOTIFIER:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_synologyNotifier(update_text.format(ipaddress), title)

    def notify_logged_error(self, ui_error: UIError):
        if settings.USE_SYNOLOGYNOTIFIER and ui_error:
            update_text = ui_error.message
            title = ui_error.title

            self._send_synologyNotifier(update_text, title)

    @staticmethod
    def _send_synologyNotifier(message, title):
        synodsmnotify_cmd = ["/usr/syno/bin/synodsmnotify", "@administrators", title, message]
        logger.info(f"Executing command {synodsmnotify_cmd}")
        logger.debug(f"Absolute path to command: {os.path.abspath(synodsmnotify_cmd[0])}")
        try:
            p = subprocess.Popen(synodsmnotify_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=settings.DATA_DIR, universal_newlines=True)
            out, err = p.communicate()
            logger.debug(_("Script result: {0}").format(str(out or err).strip()))
        except OSError as error:
            logger.info(f"Unable to run synodsmnotify: {error}")
