import re

from twilio.rest import Client, TwilioException

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):

    number_regex = re.compile(r"^\+1-\d{3}-\d{3}-\d{4}$")
    account_regex = re.compile(r"^AC[a-z0-9]{32}$")
    auth_regex = re.compile(r"^[a-z0-9]{32}$")
    phone_regex = re.compile(r"^PN[a-z0-9]{32}$")

    def notify_snatch(self, ep_name):
        if settings.TWILIO_NOTIFY_ONSNATCH:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.TWILIO_NOTIFY_ONDOWNLOAD:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyTwilio(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_git_update(self, new_version):
        if settings.USE_TWILIO:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            self._notifyTwilio(update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_TWILIO:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notifyTwilio(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        try:
            if not self.number.capabilities["sms"]:
                return False

            return self._notifyTwilio(_("This is a test notification from SickChill"), force=True, allow_raise=True)
        except TwilioException:
            return False

    @property
    def number(self):
        return self.client.api.incoming_phone_numbers.get(settings.TWILIO_PHONE_SID).fetch()

    @property
    def client(self):
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def _notifyTwilio(self, message="", force=False, allow_raise=False):
        if not (settings.USE_TWILIO or force or self.number_regex.match(settings.TWILIO_TO_NUMBER)):
            return False

        logger.debug("Sending Twilio SMS: " + message)

        try:
            self.client.messages.create(
                body=message,
                to=settings.TWILIO_TO_NUMBER,
                from_=self.number.phone_number,
            )
        except TwilioException as e:
            logger.exception("Twilio notification failed:" + str(e))

            if allow_raise:
                raise e

        return True
