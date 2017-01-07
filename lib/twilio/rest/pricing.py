from twilio.rest.base import TwilioClient
from twilio.rest.resources import UNSET_TIMEOUT
from twilio.rest.resources.pricing import (
    PhoneNumbers,
    Voice,
    MessagingCountries,
)


class TwilioPricingClient(TwilioClient):
    """
    A client for accessing the Twilio Pricing API.

    :param str account: Your Account SID from `your dashboard
        <https://twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://twilio.com/user_account>`_
    :param float timeout: The socket connect and read timeout for requests
    to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://pricing.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):
        super(TwilioPricingClient, self).__init__(account, token, base,
                                                  version, timeout,
                                                  request_account)

        self.uri_base = "{}/{}".format(base, version)

        self.voice = Voice(self.uri_base, self.auth, self.timeout)
        self.phone_numbers = PhoneNumbers(self.uri_base, self.auth,
                                          self.timeout)

    def messaging_countries(self):
        """
        Returns a :class:`MessagingCountries` resource
        :return: MessagingCountries
        """
        messaging_countries_uri = "{0}/Messaging".format(
            self.uri_base)
        return MessagingCountries(messaging_countries_uri, self.auth,
                                  self.timeout)
