from twilio.rest.base import TwilioClient
from twilio.rest.resources import UNSET_TIMEOUT
from twilio.rest.resources.ip_messaging.services import Services
from twilio.rest.resources.ip_messaging.credentials import Credentials


class TwilioIpMessagingClient(TwilioClient):
    """
    A client for accessing the Twilio IP Messaging API.

    The Twilio IP Messaging API provides information about events. For more
    information, see the
    `IP Messaging API documentation <https://www.twilio.com/docs/XXX>`_.

    :param str account: Your Account Sid from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://ip-messaging.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):

        super(TwilioIpMessagingClient, self).__init__(account, token, base,
                                                      version, timeout,
                                                      request_account)

        self.version_uri = "%s/%s" % (base, version)
        self.services = Services(self.version_uri, self.auth, timeout)
        self.credentials = Credentials(self.version_uri, self.auth, timeout)
