from twilio.rest.base import TwilioClient
from twilio.rest.resources.trunking import (
    CredentialLists,
    IpAccessControlLists,
    OriginationUrls,
    PhoneNumbers,
    Trunks
)
from twilio.rest.resources import UNSET_TIMEOUT


class TwilioTrunkingClient(TwilioClient):
    """
    A client for accessing the Twilio Trunking API

    :param str account: Your Account SID from `your dashboard
        <https://twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://trunking.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):
        """
        Create a Twilio REST API client.
        """
        super(TwilioTrunkingClient, self).__init__(account, token, base,
                                                   version, timeout,
                                                   request_account)
        self.trunk_base_uri = "{0}/{1}".format(base, version)

    def credential_lists(self, trunk_sid):
        """
        Return a :class:`CredentialList` instance
        """
        credential_lists_uri = "{0}/Trunks/{1}".format(
            self.trunk_base_uri, trunk_sid)
        return CredentialLists(credential_lists_uri, self.auth, self.timeout)

    def ip_access_control_lists(self, trunk_sid):
        """
        Return a :class:`IpAccessControlList` instance
        """
        ip_access_control_lists_uri = "{0}/Trunks/{1}".format(
            self.trunk_base_uri, trunk_sid)
        return IpAccessControlLists(ip_access_control_lists_uri, self.auth,
                                    self.timeout)

    def origination_urls(self, trunk_sid):
        """
        Return a :class:`OriginationUrls` instance
        """
        origination_urls_uri = "{0}/Trunks/{1}".format(
            self.trunk_base_uri, trunk_sid)
        return OriginationUrls(origination_urls_uri, self.auth, self.timeout)

    def phone_numbers(self, trunk_sid):
        """
        Return a :class:`PhoneNumbers` instance
        """
        phone_numbers_uri = "{0}/Trunks/{1}".format(self.trunk_base_uri,
                                                    trunk_sid)
        return PhoneNumbers(phone_numbers_uri, self.auth, self.timeout)

    def trunks(self):
        """
        Return a :class:`Trunks` instance
        """
        return Trunks(self.trunk_base_uri, self.auth, self.timeout)
