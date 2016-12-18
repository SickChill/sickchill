from twilio.rest.base import TwilioClient
from twilio.rest.resources import (
    UNSET_TIMEOUT,
    Activities,
    Events,
    Reservations,
    TaskQueues,
    Tasks,
    Workers,
    Workflows,
    Workspaces,
)


class TwilioTaskRouterClient(TwilioClient):
    """
    A client for accessing the Twilio TaskRouter API

    :param str account: Your Account SID from `your dashboard
        <https://twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://twilio.com/user/account>`_
    :param float timeout: The socket and read timeout for requests to Twilio
    """

    def __init__(self, account=None, token=None,
                 base="https://taskrouter.twilio.com", version="v1",
                 timeout=UNSET_TIMEOUT, request_account=None):
        """
        Create a Twilio REST API client.
        """
        super(TwilioTaskRouterClient, self).__init__(account, token, base,
                                                     version, timeout,
                                                     request_account)
        self.base_uri = "{0}/{1}".format(base, version)
        self.workspace_uri = "{0}/Workspaces".format(self.base_uri)

        self.workspaces = Workspaces(self.base_uri, self.auth, timeout)

    def activities(self, workspace_sid):
        """
        Return a :class:`Activities` instance for the :class:`Activity`
        with the given workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return Activities(base_uri, self.auth, self.timeout)

    def events(self, workspace_sid):
        """
        Return a :class:`Events` instance for the :class:`Event` with the given
        workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return Events(base_uri, self.auth, self.timeout)

    def reservations(self, workspace_sid, task_sid):
        """
        Return a :class:`Reservations` instance for the :class:`Reservation`
        with the given workspace_sid ans task_sid
        """
        base_uri = "{0}/{1}/Tasks/{2}".format(self.workspace_uri,
                                              workspace_sid, task_sid)
        return Reservations(base_uri, self.auth, self.timeout)

    def worker_reservations(self, workspace_sid, worker_sid):
        """
        Return a :class:`Reservations` instance for the :class:`Reservation`
        with the given workspace_sid ans worker_sid
        """
        base_uri = "{0}/{1}/Workers/{2}".format(self.workspace_uri,
                                                workspace_sid, worker_sid)
        return Reservations(base_uri, self.auth, self.timeout)

    def task_queues(self, workspace_sid):
        """
        Return a :class:`TaskQueues` instance for the :class:`TaskQueue` with
        the given workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return TaskQueues(base_uri, self.auth, self.timeout)

    def tasks(self, workspace_sid):
        """
        Return a :class:`Tasks` instance for the :class:`Task` with the given
        workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return Tasks(base_uri, self.auth, self.timeout)

    def workers(self, workspace_sid):
        """
        Return a :class:`Workers` instance for the :class:`Worker` with the
        given workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return Workers(base_uri, self.auth, self.timeout)

    def workflows(self, workspace_sid):
        """
        Return a :class:`Workflows` instance for the :class:`Workflow` with the
        given workspace_sid
        """
        base_uri = "{0}/{1}".format(self.workspace_uri, workspace_sid)
        return Workflows(base_uri, self.auth, self.timeout)
