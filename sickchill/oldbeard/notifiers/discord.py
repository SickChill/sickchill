from sickchill import settings
from sickchill.oldbeard import common


class Notifier(object):
    def notify_snatch(self, ep_name):
        if settings.DISCORD_NOTIFY_SNATCH:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.DISCORD_NOTIFY_DOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.DISCORD_NOTIFY_SUBTITLEDOWNLOAD:
            self._notify_discord(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_git_update(self, new_version="??"):
        if settings.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_discord(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_DISCORD:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_discord(title + " - " + update_text.format(ipaddress))

    def test_notify(self, webhook: str = None, name: str = None, avatar: str = None, tts=None):
        from sickchill.oldbeard.notifications_queue import DiscordTask

        task = DiscordTask("This is a test notification from SickChill")
        return task._send_discord(webhook=webhook, name=name, avatar=avatar, tts=tts)

    @staticmethod
    def _send_discord(message=None, force=False):
        return settings.notificationsTaskScheduler.action.add_item(message, notifier="discord", force_next=force)

    def _notify_discord(self, message="", force=False):
        if not settings.USE_DISCORD and not force:
            return False

        return self._send_discord(message, force=force)
