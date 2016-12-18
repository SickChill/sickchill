from twilio.rest.base import TwilioClient
from twilio.rest.resources import (
    UNSET_TIMEOUT,
    Accounts,
    Addresses,
    Applications,
    AuthorizedConnectApps,
    CallFeedback,
    CallFeedbackFactory,
    CallerIds,
    Calls,
    Conferences,
    ConnectApps,
    DependentPhoneNumbers,
    Keys,
    MediaList,
    Members,
    Messages,
    Notifications,
    Participants,
    PhoneNumbers,
    Queues,
    Recordings,
    Sandboxes,
    Sip,
    Sms,
    Tokens,
    Transcriptions,
    Usage,
)


class TwilioRestClient(TwilioClient):
    """
    A client for accessing the Twilio REST API

    :param str account: Your Account SID from `your dashboard
        <https://twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None, base="https://api.twilio.com",
                 version="2010-04-01", timeout=UNSET_TIMEOUT,
                 request_account=None):
        """
        Create a Twilio REST API client.
        """
        super(TwilioRestClient, self).__init__(account, token, base, version,
                                               timeout, request_account)

        version_uri = "%s/%s" % (base, version)

        self.accounts = Accounts(version_uri, self.auth, timeout)
        self.applications = Applications(self.account_uri, self.auth, timeout)
        self.authorized_connect_apps = AuthorizedConnectApps(
            self.account_uri,
            self.auth,
            timeout
        )
        self.addresses = Addresses(self.account_uri, self.auth, timeout)
        self.calls = Calls(self.account_uri, self.auth, timeout)
        self.caller_ids = CallerIds(self.account_uri, self.auth, timeout)
        self.connect_apps = ConnectApps(self.account_uri, self.auth, timeout)
        self.notifications = Notifications(self.account_uri, self.auth,
                                           timeout)
        self.recordings = Recordings(self.account_uri, self.auth, timeout)
        self.transcriptions = Transcriptions(self.account_uri, self.auth,
                                             timeout)
        self.sms = Sms(self.account_uri, self.auth, timeout)
        self.phone_numbers = PhoneNumbers(self.account_uri, self.auth, timeout)
        self.conferences = Conferences(self.account_uri, self.auth, timeout)
        self.queues = Queues(self.account_uri, self.auth, timeout)
        self.sandboxes = Sandboxes(self.account_uri, self.auth, timeout)
        self.usage = Usage(self.account_uri, self.auth, timeout)
        self.messages = Messages(self.account_uri, self.auth, timeout)
        self.media = MediaList(self.account_uri, self.auth, timeout)
        self.sip = Sip(self.account_uri, self.auth, timeout)
        self.tokens = Tokens(self.account_uri, self.auth, timeout)
        self.keys = Keys(self.account_uri, self.auth, timeout)

    def participants(self, conference_sid):
        """
        Return a :class:`~twilio.rest.resources.Participants` instance for the
        :class:`~twilio.rest.resources.Conference` with given conference_sid
        """
        base_uri = "%s/Conferences/%s" % (self.account_uri, conference_sid)
        return Participants(base_uri, self.auth, self.timeout)

    def members(self, queue_sid):
        """
        Return a :class:`Members <twilio.rest.resources.Members>` instance for
        the :class:`Queue <twilio.rest.resources.Queue>` with the
        given queue_sid
        """
        base_uri = "%s/Queues/%s" % (self.account_uri, queue_sid)
        return Members(base_uri, self.auth, self.timeout)

    def feedback(self, call_sid):
        """
        Return a :class:`CallFeedback <twilio.rest.resources.CallFeedback>`
        instance for the :class:`Call <twilio.rest.resources.calls.Call>`
        with the given call_sid
        """
        base_uri = "%s/Calls/%s/Feedback" % (self.account_uri, call_sid)
        call_feedback_list = CallFeedbackFactory(
            base_uri,
            self.auth,
            self.timeout
        )
        return CallFeedback(call_feedback_list)

    def dependent_phone_numbers(self, address_sid):
        """
        Return a :class:`DependentPhoneNumbers
        <twilio.rest.resources.DependentPhoneNumbers>` instance for the
        :class:`Address <twilio.rest.resources.Address>` with the given
        address_sid
        """
        base_uri = "%s/Addresses/%s" % (self.account_uri, address_sid)
        return DependentPhoneNumbers(base_uri, self.auth, self.timeout)
