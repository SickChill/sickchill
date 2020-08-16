# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
import urllib.parse
import urllib.request

from sickchill import logger, settings
from sickchill.helper import HTTP_STATUS_CODES
from sickchill.oldbeard.common import (NOTIFY_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, NOTIFY_LOGIN, NOTIFY_LOGIN_TEXT, NOTIFY_SNATCH,
                                       NOTIFY_SUBTITLE_DOWNLOAD, notifyStrings)


class Notifier(object):
    """
    Use Telegram to send notifications

    https://telegram.org/
    """

    def test_notify(self, id=None, api_key=None):
        """
        Send a test notification
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :returns: the notification
        """
        return self._notify_telegram('Test', 'This is a test notification from SickChill', id, api_key, force=True)

    @staticmethod
    def _send_telegram_msg(title, msg, id=None, api_key=None):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param msg: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token

        :returns: True if the message succeeded, False otherwise
        """
        id = settings.TELEGRAM_ID if id is None else id
        api_key = settings.TELEGRAM_APIKEY if api_key is None else api_key

        logger.debug('Telegram in use with API KEY: {0}'.format(api_key))

        message = '{0} : {1}'.format(title, msg)
        payload = urllib.parse.urlencode({'chat_id': id, 'text': message})
        telegram_api = 'https://api.telegram.org/bot%s/%s'

        req = urllib.request.Request(telegram_api % (api_key, 'sendMessage'), payload.encode())

        success = False
        try:
            urllib.request.urlopen(req)
            message = 'Telegram message sent successfully.'
            success = True
        except IOError as e:
            message = 'Unknown IO error: {0}'.format(e)
            if hasattr(e, 'code'):
                error_message = {
                    400: 'Missing parameter(s). Double check your settings or if the channel/user exists.',
                    401: 'Authentication failed.',
                    420: 'Too many messages.',
                    500: 'Server error. Please retry in a few moments.',
                }
                if e.code in error_message:
                    message = error_message.get(e.code)
                else:
                    message = HTTP_STATUS_CODES.get(e.code, message)
        except Exception as e:
            message = 'Error while sending Telegram message: {0} '.format(e)
        finally:
            logger.info(message)
            return success, message

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        """
        Sends a Telegram notification when an episode is snatched

        :param ep_name: The name of the episode snatched
        :param title: The title of the notification to send
        """
        if settings.TELEGRAM_NOTIFY_ONSNATCH:
            self._notify_telegram(title, ep_name)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        """
        Sends a Telegram notification when an episode is downloaded

        :param ep_name: The name of the episode downloaded
        :param title: The title of the notification to send
        """
        if settings.TELEGRAM_NOTIFY_ONDOWNLOAD:
            self._notify_telegram(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        """
        Sends a Telegram notification when subtitles for an episode are downloaded

        :param ep_name: The name of the episode subtitles were downloaded for
        :param lang: The language of the downloaded subtitles
        :param title: The title of the notification to send
        """
        if settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_telegram(title, '{0}: {1}'.format(ep_name, lang))

    def notify_git_update(self, new_version='??'):
        """
        Sends a Telegram notification for git updates

        :param new_version: The new version available from git
        """
        if settings.USE_TELEGRAM:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notify_telegram(title, update_text + new_version)

    def notify_login(self, ipaddress=''):
        """
        Sends a Telegram notification on login

        :param ipaddress: The ip address the login is originating from
        """
        if settings.USE_TELEGRAM:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notify_telegram(title, update_text.format(ipaddress))

    def _notify_telegram(self, title, message, id=None, api_key=None, force=False):
        """
        Sends a Telegram notification

        :param title: The title of the notification to send
        :param message: The message string to send
        :param id: The Telegram user/group id to send the message to
        :param api_key: Your Telegram bot API token
        :param force: Enforce sending, for instance for testing

        :returns: the message to send
        """

        if not (force or settings.USE_TELEGRAM):
            logger.debug('Notification for Telegram not enabled, skipping this notification')
            return False, 'Disabled'

        logger.debug('Sending a Telegram message for {0}'.format(message))

        return self._send_telegram_msg(title, message, id, api_key)
