import requests
from requests_oauthlib import OAuth1Session

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    consumer_key = "vHHtcB6WzpWDG6KYlBMr8g"
    consumer_hash = "zMqq5CB3f8cWKiRO2KzWPTlBanYmV0VYxSXZ0Pxds0E"  # (consumer_secret)

    REQUEST_TOKEN_URL = "https://api.x.com/oauth/request_token"
    ACCESS_TOKEN_URL = "https://api.x.com/oauth/access_token"
    AUTHORIZATION_URL = "https://api.x.com/oauth/authorize"
    API_BASE = "https://api.x.com/1.1"

    def _api_session(self):
        return OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_hash,
            resource_owner_key=settings.TWITTER_USERNAME,
            resource_owner_secret=settings.TWITTER_PASSWORD,
        )

    def notify_snatch(self, ep_name):
        if settings.TWITTER_NOTIFY_ONSNATCH:
            self._notify_twitter(common.notifyStrings[common.NOTIFY_SNATCH] + ": " + ep_name)

    def notify_download(self, ep_name):
        if settings.TWITTER_NOTIFY_ONDOWNLOAD:
            self._notify_twitter(common.notifyStrings[common.NOTIFY_DOWNLOAD] + ": " + ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_twitter(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD] + " " + ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        if settings.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_UPDATE]
            self._notify_twitter(title + " - " + update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_TWITTER:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_twitter(title + " - " + update_text.format(ipaddress))

    def test_notify(self):
        """
        Tests sending notification.

        :return: True if succeeded, False otherwise
        """
        return self._notify_twitter("This is a test notification from SickChill", force=True)

    def _get_authorization(self):
        """
        Step 1 of authorization - get app authorization url.

        :return: True if succeeded, False otherwise
        """
        logger.debug("Requesting temp token from Twitter")
        oauth_session = OAuth1Session(client_key=self.consumer_key, client_secret=self.consumer_hash)

        try:
            request_token = oauth_session.fetch_request_token(self.REQUEST_TOKEN_URL)
        except requests.exceptions.RequestException as error:
            logger.exception(f"Invalid response from Twitter requesting temp token: {error}")
        else:
            settings.TWITTER_USERNAME = request_token["oauth_token"]
            settings.TWITTER_PASSWORD = request_token["oauth_token_secret"]
            return oauth_session.authorization_url(self.AUTHORIZATION_URL)

    def _get_credentials(self, key):
        logger.info("Type of key is {}".format(type(key)))
        """
        Step 2 of authorization - poll server for access token.

        :param key: Authorization key received from twitter
        :return: True if succeeded, False otherwise
        """
        logger.debug("Generating and signing request for an access token using key " + key)
        oauth_session = OAuth1Session(
            client_key=self.consumer_key,
            client_secret=self.consumer_hash,
            resource_owner_key=settings.TWITTER_USERNAME,
            resource_owner_secret=settings.TWITTER_PASSWORD,
        )

        try:
            access_token = oauth_session.fetch_access_token(self.ACCESS_TOKEN_URL, verifier=str(key))
        except Exception as error:
            logger.exception(f"The request for a token with did not succeed: {error}")
            return False

        logger.debug("Your Twitter Access Token key: {0}".format(access_token["oauth_token"]))
        logger.debug("Access Token secret: {0}".format(access_token["oauth_token_secret"]))
        settings.TWITTER_USERNAME = access_token["oauth_token"]
        settings.TWITTER_PASSWORD = access_token["oauth_token_secret"]
        return True

    def _send_tweet(self, message=None):
        """
        Sends a tweet.

        :param message: Message to send
        :return: True if succeeded, False otherwise
        """
        logger.debug("Sending tweet: {}".format(message))
        try:
            response = self._api_session().post(f"{self.API_BASE}/statuses/update.json", data={"status": (message or "")[:139]})
            response.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Tweet: {error}")
            return False

        return True

    def _send_dm(self, message=None):
        """
        Sends a direct message.

        :param message: Message to send
        :return: True if succeeded, False otherwise
        """
        dmdest = settings.TWITTER_DMTO

        logger.debug("Sending DM @{0}: {1}".format(dmdest, message))
        try:
            session = self._api_session()
            user = session.get(f"{self.API_BASE}/users/show.json", params={"screen_name": dmdest})
            user.raise_for_status()
            user_id = user.json()["id"]
            event = {
                "event": {
                    "type": "message_create",
                    "message_create": {
                        "target": {"recipient_id": user_id},
                        "message_data": {"text": (message or "")[:139]},
                    },
                }
            }
            response = session.post(f"{self.API_BASE}/direct_messages/events/new.json", json=event)
            response.raise_for_status()
        except Exception as error:
            logger.exception(f"Error Sending Tweet (DM): {error}")
            return False

        return True

    def _notify_twitter(self, message="", force=False):
        prefix = settings.TWITTER_PREFIX

        if not settings.USE_TWITTER and not force:
            return False

        if settings.TWITTER_USEDM and settings.TWITTER_DMTO:
            return self._send_dm(prefix + ": " + message)
        else:
            return self._send_tweet(prefix + ": " + message)
