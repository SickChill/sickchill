from twilio.rest.base import TwilioClient
from twilio.rest.resources import UNSET_TIMEOUT
from twilio.rest.resources.monitor.alerts import Alerts
from twilio.rest.resources.monitor.events import Events


class TwilioMonitorClient(TwilioClient):
    """
    A client for accessing the Twilio Monitor API.

    The Twilio Monitor API provides information about events. For more
    information, see the
    `Monitor API documentation <https://www.twilio.com/docs/XXX>`_.

    :param str account: Your Account Sid from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://monitor.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):

        super(TwilioMonitorClient, self).__init__(account, token, base,
                                                  version, timeout,
                                                  request_account)

        self.version_uri = "%s/%s" % (base, version)
        self.events = Events(self.version_uri, self.auth, timeout)
        self.alerts = Alerts(self.version_uri, self.auth, timeout)
