from urllib.parse import urljoin

from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard import common, helpers


class Notifier(object):
    def __init__(self):
        self.session = helpers.make_session()
        self.url = "https://api.pushbullet.com/v2/"

    def test_notify(self, pushbullet_api):
        logger.debug("Sending a test Pushbullet notification.")
        return self._sendPushbullet(pushbullet_api, event="Test", message="Testing Pushbullet settings from SickChill", force=True)

    def get_devices(self, pushbullet_api):
        logger.debug("Testing Pushbullet authentication and retrieving the device list.")
        headers = CaseInsensitiveDict({"Access-Token": pushbullet_api})
        return helpers.getURL(urljoin(self.url, "devices"), session=self.session, headers=headers, returns="text") or {}

    def get_channels(self, pushbullet_api):
        """Fetches the list of channels a given access key has permissions to push to"""
        logger.debug("Testing Pushbullet authentication and retrieving the device list.")
        headers = CaseInsensitiveDict({"Access-Token": pushbullet_api})
        return helpers.getURL(urljoin(self.url, "channels"), session=self.session, headers=headers, returns="text") or {}

    def notify_snatch(self, ep_name):
        if settings.PUSHBULLET_NOTIFY_ONSNATCH:
            self._sendPushbullet(pushbullet_api=None, event=common.notifyStrings[common.NOTIFY_SNATCH] + " : " + ep_name, message=ep_name)

    def notify_download(self, ep_name):
        if settings.PUSHBULLET_NOTIFY_ONDOWNLOAD:
            self._sendPushbullet(pushbullet_api=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD] + " : " + ep_name, message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushbullet(
                pushbullet_api=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " : " + ep_name + " : " + lang, message=ep_name + ": " + lang
            )

    def notify_git_update(self, new_version="??"):
        self._sendPushbullet(
            pushbullet_api=None,
            event=common.notifyStrings[common.NOTIFY_GIT_UPDATE],
            message=common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT] + new_version,
            # link=link
        )

    def notify_login(self, ipaddress=""):
        self._sendPushbullet(
            pushbullet_api=None, event=common.notifyStrings[common.NOTIFY_LOGIN], message=common.notifyStrings[common.NOTIFY_LOGIN_TEXT].format(ipaddress)
        )

    def _sendPushbullet(self, pushbullet_api=None, pushbullet_device=None, pushbullet_channel=None, event=None, message=None, link=None, force=False):

        if not (settings.USE_PUSHBULLET or force):
            return False

        pushbullet_api = pushbullet_api or settings.PUSHBULLET_API
        pushbullet_device = pushbullet_device or settings.PUSHBULLET_DEVICE
        pushbullet_channel = pushbullet_channel or settings.PUSHBULLET_CHANNEL

        logger.debug("Pushbullet event: {0!r}".format(event))
        logger.debug("Pushbullet message: {0!r}".format(message))
        logger.debug("Pushbullet api: {0!r}".format(pushbullet_api))
        logger.debug("Pushbullet devices: {0!r}".format(pushbullet_device))

        post_data = {"title": event, "body": message, "type": "link" if link else "note"}
        if link:
            post_data["url"] = link

        headers = CaseInsensitiveDict({"Access-Token": pushbullet_api})

        if pushbullet_device:
            post_data["device_iden"] = pushbullet_device
        elif pushbullet_channel:
            post_data["channel_tag"] = pushbullet_channel

        response = helpers.getURL(urljoin(self.url, "pushes"), session=self.session, post_data=post_data, headers=headers, returns="json") or {}

        failed = response.pop("error", {})
        if failed:
            logger.warning("Pushbullet notification failed: {0}".format(failed.pop("message")))
        else:
            logger.debug("Pushbullet notification sent.")

        return False if failed else True
