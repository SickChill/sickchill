from . import InstanceResource, ListResource
from .applications import Applications
from .notifications import Notifications
from .recordings import Transcriptions, Recordings
from .calls import Calls
from .sms_messages import Sms
from .caller_ids import CallerIds
from .phone_numbers import PhoneNumbers
from .conferences import Conferences
from .connect_apps import ConnectApps, AuthorizedConnectApps
from .queues import Queues
from .keys import Keys
from .usage import UsageRecords, UsageTriggers
from .messages import Messages
from .media import MediaList
from .sip import Sip


class Account(InstanceResource):
    """ An Account resource

    """

    ACTIVE = "active"        #: A constant representing an active account
    SUSPENDED = "suspended"  #: A constant representing a suspended account
    CLOSED = "closed"        #: A constant representing a closed account

    subresources = [
        Applications,
        Notifications,
        Transcriptions,
        Recordings,
        Calls,
        Sms,
        CallerIds,
        PhoneNumbers,
        Conferences,
        ConnectApps,
        Queues,
        AuthorizedConnectApps,
        UsageRecords,
        UsageTriggers,
        MediaList,
        Messages,
        Sip,
        Keys,
    ]

    def update(self, **kwargs):
        """
        Update the status of an account.

        :param friendly_name: Update the description of this account.
        :param status: Alter the status of this account

        Use :const:`CLOSED` to irreversibly close this account,
        :const:`SUSPENDED` to temporarily suspend it, or :const:`ACTIVE`
        to reactivate it.
        """
        self.update_instance(**kwargs)

    def close(self):
        """
        Permenently deactivate this account
        """
        return self.update_instance(status=Account.CLOSED)

    def suspend(self):
        """
        Temporarily suspend this account
        """
        return self.update_instance(status=Account.SUSPENDED)

    def activate(self):
        """
        Reactivate this account
        """
        return self.update_instance(status=Account.ACTIVE)


class Accounts(ListResource):
    """ A list of Account resources """

    name = "Accounts"
    instance = Account

    def list(self, **kwargs):
        """
        Returns a page of :class:`Account` resources as a list. For paging
        informtion see :class:`ListResource`

        :param date friendly_name: Only list accounts with this friendly name
        :param date status: Only list accounts with this status
        """
        return self.get_instances(kwargs)

    def update(self, sid, **kwargs):
        """
        :param sid: Account identifier
        :param friendly_name: Update the description of this account.
        :param status: Alter the status of this account

        Use :data:`CLOSED` to irreversibly close this account,
        :data:`SUSPENDED` to temporarily suspend it, or :data:`ACTIVE`
        to reactivate it.
        """
        return self.update_instance(sid, kwargs)

    def close(self, sid):
        """
        Permenently deactivate an account, Alias to update
        """
        return self.update(sid, status=Account.CLOSED)

    def suspend(self, sid):
        """
        Temporarily suspend an account, Alias to update
        """
        return self.update(sid, status=Account.SUSPENDED)

    def activate(self, sid):
        """
        Reactivate an account, Alias to update
        """
        return self.update(sid, status=Account.ACTIVE)

    def create(self, **kwargs):
        """
        Returns a newly created sub account resource.

        :param friendly_name: Update the description of this account.
        """
        return self.create_instance(kwargs)
