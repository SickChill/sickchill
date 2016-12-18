from . import InstanceResource, ListResource
from .util import UNSET_TIMEOUT


class UsageTrigger(InstanceResource):
    """ A usage trigger resource """

    def update(self, **kwargs):
        """
        Update this usage trigger
        """
        return self.parent.update(self.name, **kwargs)

    def delete(self):
        """
        Delete this usage trigger
        """
        return self.parent.delete(self.name)


class UsageTriggers(ListResource):
    name = "Usage/Triggers"
    instance = UsageTrigger
    key = "usage_triggers"

    def list(self, **kwargs):
        """
        Returns a page of :class:`UsageTrigger` resources as a list. For paging
        information see :class:`ListResource`

        :param recurring: Only show UsageTriggers that count over this
                          interval. One of daily, monthly, or yearly. To
                          retrieve non-recurring triggers, leave this empty or
                          use alltime.
        :param usage_category: Only show UsageTriggers that watch this usage
                               category. Must be one of the supported usage
                               categories.
        :trigger_by: Only show UsageTriggers that trigger by this field in the
                     UsageRecord. Must be one of: count, usage, or price as
                     described in the UsageRecords documentation.
        """
        return self.get_instances(kwargs)

    def create(self, **kwargs):
        """
        Create an :class:`UsageTrigger` with any of these optional parameters.

        :param friendly_name: A human readable description of the UsageTrigger,
                              with maximum length 64 characters.
        :param usage_category: The trigger will watch this usage category.
        :param trigger_value: The trigger will fire when usage reaches this
                              value.
        :param callback_url: Twilio will make a request to this url when the
                             trigger fires.
        :param trigger_by: The field in the UsageRecord that will fire the
                           trigger. One of count, usage, or price as described
                           in the UsageRecords documentation. The default is
                           usage.
        :param recurring: The interval the trigger will count over. Must be one
                          of: daily, monthly, or yearly. Omit this to create a
                          non-recurring trigger.
        :param callback_method: Twilio will use this HTTP method when making a
                                request to the CallbackUrl. GET or POST. The
                                default is POST.
        """
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """ Update the UsageTrigger with the given sid to have the kwargs """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`UsageTrigger`
        """
        return self.delete_instance(sid)


class UsageRecord(InstanceResource):
    """ A usage record resource """

    def load(self, entries):
        uri = entries.get('uri')
        super(UsageRecord, self).load(entries)
        self.__dict__.update({'uri': uri})

    @property
    def uri(self):
        return self.__dict__.get('uri')


class BaseUsageRecords(ListResource):
    name = "Usage/Records"
    instance = UsageRecord
    key = "usage_records"

    def list(self, **kwargs):
        """
        Returns a page of :class:`UsageRecord` resources as a list. For paging
        information see :class:`ListResource`

        :param category: Only include usage of this usage category.
        :param start_date: Only include usage that has occurred on or after
                           this date. Format is YYYY-MM-DD. All dates are in
                           GMT.
        :param end_date: Only include usage that has occurred on or before this
                         date. Format is YYYY-MM-DD. All dates are in GMT.
        """
        return self.get_instances(kwargs)

    def get(self, *args, **kwargs):
        raise AttributeError('Unsupported in UsageRecords')

    def load_instance(self, data):
        instance = self.instance(self, "Resource")
        instance.load(data)
        instance.load_subresources()
        return instance


class UsageRecords(BaseUsageRecords):

    def __init__(self, base_uri, auth, timeout=UNSET_TIMEOUT):
        super(UsageRecords, self).__init__(base_uri, auth, timeout)
        self.daily = UsageRecordsDaily(base_uri, auth, timeout)
        self.monthly = UsageRecordsMonthly(base_uri, auth, timeout)
        self.yearly = UsageRecordsYearly(base_uri, auth, timeout)
        self.today = UsageRecordsToday(base_uri, auth, timeout)
        self.yesterday = UsageRecordsYesterday(base_uri, auth, timeout)
        self.this_month = UsageRecordsThisMonth(base_uri, auth, timeout)
        self.last_month = UsageRecordsLastMonth(base_uri, auth, timeout)


class UsageRecordsDaily(BaseUsageRecords):
    name = "Usage/Records/Daily"


class UsageRecordsMonthly(BaseUsageRecords):
    name = "Usage/Records/Monthly"


class UsageRecordsYearly(BaseUsageRecords):
    name = "Usage/Records/Yearly"


class UsageRecordsToday(BaseUsageRecords):
    name = "Usage/Records/Today"


class UsageRecordsYesterday(BaseUsageRecords):
    name = "Usage/Records/Yesterday"


class UsageRecordsThisMonth(BaseUsageRecords):
    name = "Usage/Records/ThisMonth"


class UsageRecordsLastMonth(BaseUsageRecords):
    name = "Usage/Records/LastMonth"

UsageRecord.subresources = [
    UsageRecordsDaily,
    UsageRecordsMonthly,
    UsageRecordsYearly,
    UsageRecordsToday,
    UsageRecordsYesterday,
    UsageRecordsThisMonth,
    UsageRecordsLastMonth
]


class Usage(object):
    """
    Holds all the specific Usage list resources
    """

    def __init__(self, base_uri, auth, timeout=UNSET_TIMEOUT):
        self.records = UsageRecords(base_uri, auth, timeout=timeout)
        self.triggers = UsageTriggers(base_uri, auth, timeout=timeout)
        self.timeout = timeout
