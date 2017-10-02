from twilio.rest.base import TwilioClient
from twilio.rest.resources import UNSET_TIMEOUT
from twilio.rest.resources.lookups.phone_numbers import PhoneNumbers


class TwilioLookupsClient(TwilioClient):
    """
    A client for accessing the Twilio Lookups API.

    The Twilio Lookups API provides information about phone numbers,
    including non-Twilio numbers. For more information, see the
    `Lookups API documentation <https://www.twilio.com/docs/XXX>`_.

    :param str account: Your Account Sid from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://www.twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://lookups.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):

        super(TwilioLookupsClient, self).__init__(account, token, base,
                                                  version, timeout,
                                                  request_account)

        self.version_uri = "%s/%s" % (base, version)
        self.phone_numbers = PhoneNumbers(self.version_uri, self.auth, timeout)
