import sickchill
from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    def __init__(self):
        self.session = sickchill.oldbeard.helpers.make_session()

    def test_notify(self, pushalot_authorizationtoken):
        return self._sendPushalot(
            pushalot_authorizationtoken=pushalot_authorizationtoken, event="Test", message="Testing Pushalot settings from SickChill", force=True
        )

    def notify_snatch(self, ep_name):
        if settings.PUSHALOT_NOTIFY_ONSNATCH:
            self._sendPushalot(pushalot_authorizationtoken=None, event=common.notifyStrings[common.NOTIFY_SNATCH], message=ep_name)

    def notify_download(self, ep_name):
        if settings.PUSHALOT_NOTIFY_ONDOWNLOAD:
            self._sendPushalot(pushalot_authorizationtoken=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD], message=ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendPushalot(
                pushalot_authorizationtoken=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], message="{0}:{1}".format(ep_name, lang)
            )

    def notify_git_update(self, new_version="??"):
        update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
        self._sendPushalot(pushalot_authorizationtoken=None, event=title, message=update_text + new_version)

    def notify_login(self, ipaddress=""):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._sendPushalot(pushalot_authorizationtoken=None, event=title, message=update_text.format(ipaddress))

    def _sendPushalot(self, pushalot_authorizationtoken=None, event=None, message=None, force=False):

        if not (settings.USE_PUSHALOT or force):
            return False

        pushalot_authorizationtoken = pushalot_authorizationtoken or settings.PUSHALOT_AUTHORIZATIONTOKEN

        logger.debug("Pushalot event: {0}".format(event))
        logger.debug("Pushalot message: {0}".format(message))
        logger.debug("Pushalot api: {0}".format(pushalot_authorizationtoken))

        post_data = {"AuthorizationToken": pushalot_authorizationtoken, "Title": event or "", "Body": message or ""}

        jdata = sickchill.oldbeard.helpers.getURL("https://pushalot.com/api/sendmessage", post_data=post_data, session=self.session, returns="json") or {}

        """
        {'Status': 200, 'Description': 'The request has been completed successfully.', 'Success': True}
        """

        success = jdata.pop("Success", False)
        if success:
            logger.debug("Pushalot notifications sent.")
        else:
            logger.error("Pushalot notification failed: {0} {1}".format(jdata.get("Status", ""), jdata.get("Description", "Unknown")))

        return success
