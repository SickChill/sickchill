# coding=utf-8
r"""
This code was generated by
\ / _    _  _|   _  _
 | (_)\/(_)(_|\/| |(/_  v1.0.0
      /       /
"""

from twilio.base import deserialize
from twilio.base import values
from twilio.base.instance_context import InstanceContext
from twilio.base.instance_resource import InstanceResource
from twilio.base.list_resource import ListResource
from twilio.base.page import Page


class SubscribedEventList(ListResource):
    """ PLEASE NOTE that this class contains preview products that are subject
    to change. Use them with caution. If you currently do not have developer
    preview access, please contact help@twilio.com. """

    def __init__(self, version, subscription_sid):
        """
        Initialize the SubscribedEventList

        :param Version version: Version that contains the resource
        :param subscription_sid: The subscription_sid

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventList
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventList
        """
        super(SubscribedEventList, self).__init__(version)

        # Path Solution
        self._solution = {'subscription_sid': subscription_sid, }
        self._uri = '/Subscriptions/{subscription_sid}/SubscribedEvents'.format(**self._solution)

    def stream(self, limit=None, page_size=None):
        """
        Streams SubscribedEventInstance records from the API as a generator stream.
        This operation lazily loads records as efficiently as possible until the limit
        is reached.
        The results are returned as a generator, so this operation is memory efficient.

        :param int limit: Upper limit for the number of records to return. stream()
                          guarantees to never return more than limit.  Default is no limit
        :param int page_size: Number of records to fetch per request, when not set will use
                              the default value of 50 records.  If no page_size is defined
                              but a limit is defined, stream() will attempt to read the
                              limit with the most efficient page size, i.e. min(limit, 1000)

        :returns: Generator that will yield up to limit results
        :rtype: list[twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance]
        """
        limits = self._version.read_limits(limit, page_size)

        page = self.page(page_size=limits['page_size'], )

        return self._version.stream(page, limits['limit'])

    def list(self, limit=None, page_size=None):
        """
        Lists SubscribedEventInstance records from the API as a list.
        Unlike stream(), this operation is eager and will load `limit` records into
        memory before returning.

        :param int limit: Upper limit for the number of records to return. list() guarantees
                          never to return more than limit.  Default is no limit
        :param int page_size: Number of records to fetch per request, when not set will use
                              the default value of 50 records.  If no page_size is defined
                              but a limit is defined, list() will attempt to read the limit
                              with the most efficient page size, i.e. min(limit, 1000)

        :returns: Generator that will yield up to limit results
        :rtype: list[twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance]
        """
        return list(self.stream(limit=limit, page_size=page_size, ))

    def page(self, page_token=values.unset, page_number=values.unset,
             page_size=values.unset):
        """
        Retrieve a single page of SubscribedEventInstance records from the API.
        Request is executed immediately

        :param str page_token: PageToken provided by the API
        :param int page_number: Page Number, this value is simply for client state
        :param int page_size: Number of records to return, defaults to 50

        :returns: Page of SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventPage
        """
        data = values.of({'PageToken': page_token, 'Page': page_number, 'PageSize': page_size, })

        response = self._version.page(method='GET', uri=self._uri, params=data, )

        return SubscribedEventPage(self._version, response, self._solution)

    def get_page(self, target_url):
        """
        Retrieve a specific page of SubscribedEventInstance records from the API.
        Request is executed immediately

        :param str target_url: API-generated URL for the requested results page

        :returns: Page of SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventPage
        """
        response = self._version.domain.twilio.request(
            'GET',
            target_url,
        )

        return SubscribedEventPage(self._version, response, self._solution)

    def create(self, type, version=values.unset):
        """
        Create the SubscribedEventInstance

        :param unicode type: The type
        :param unicode version: The version

        :returns: The created SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        """
        data = values.of({'Type': type, 'Version': version, })

        payload = self._version.create(method='POST', uri=self._uri, data=data, )

        return SubscribedEventInstance(
            self._version,
            payload,
            subscription_sid=self._solution['subscription_sid'],
        )

    def get(self, type):
        """
        Constructs a SubscribedEventContext

        :param type: The type

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        """
        return SubscribedEventContext(
            self._version,
            subscription_sid=self._solution['subscription_sid'],
            type=type,
        )

    def __call__(self, type):
        """
        Constructs a SubscribedEventContext

        :param type: The type

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        """
        return SubscribedEventContext(
            self._version,
            subscription_sid=self._solution['subscription_sid'],
            type=type,
        )

    def __repr__(self):
        """
        Provide a friendly representation

        :returns: Machine friendly representation
        :rtype: str
        """
        return '<Twilio.Events.V1.SubscribedEventList>'


class SubscribedEventPage(Page):
    """ PLEASE NOTE that this class contains preview products that are subject
    to change. Use them with caution. If you currently do not have developer
    preview access, please contact help@twilio.com. """

    def __init__(self, version, response, solution):
        """
        Initialize the SubscribedEventPage

        :param Version version: Version that contains the resource
        :param Response response: Response from the API
        :param subscription_sid: The subscription_sid

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventPage
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventPage
        """
        super(SubscribedEventPage, self).__init__(version, response)

        # Path Solution
        self._solution = solution

    def get_instance(self, payload):
        """
        Build an instance of SubscribedEventInstance

        :param dict payload: Payload response from the API

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        """
        return SubscribedEventInstance(
            self._version,
            payload,
            subscription_sid=self._solution['subscription_sid'],
        )

    def __repr__(self):
        """
        Provide a friendly representation

        :returns: Machine friendly representation
        :rtype: str
        """
        return '<Twilio.Events.V1.SubscribedEventPage>'


class SubscribedEventContext(InstanceContext):
    """ PLEASE NOTE that this class contains preview products that are subject
    to change. Use them with caution. If you currently do not have developer
    preview access, please contact help@twilio.com. """

    def __init__(self, version, subscription_sid, type):
        """
        Initialize the SubscribedEventContext

        :param Version version: Version that contains the resource
        :param subscription_sid: The subscription_sid
        :param type: The type

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        """
        super(SubscribedEventContext, self).__init__(version)

        # Path Solution
        self._solution = {'subscription_sid': subscription_sid, 'type': type, }
        self._uri = '/Subscriptions/{subscription_sid}/SubscribedEvents/{type}'.format(**self._solution)

    def update(self, version):
        """
        Update the SubscribedEventInstance

        :param unicode version: The version

        :returns: The updated SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        """
        data = values.of({'Version': version, })

        payload = self._version.update(method='POST', uri=self._uri, data=data, )

        return SubscribedEventInstance(
            self._version,
            payload,
            subscription_sid=self._solution['subscription_sid'],
            type=self._solution['type'],
        )

    def delete(self):
        """
        Deletes the SubscribedEventInstance

        :returns: True if delete succeeds, False otherwise
        :rtype: bool
        """
        return self._version.delete(method='DELETE', uri=self._uri, )

    def __repr__(self):
        """
        Provide a friendly representation

        :returns: Machine friendly representation
        :rtype: str
        """
        context = ' '.join('{}={}'.format(k, v) for k, v in self._solution.items())
        return '<Twilio.Events.V1.SubscribedEventContext {}>'.format(context)


class SubscribedEventInstance(InstanceResource):
    """ PLEASE NOTE that this class contains preview products that are subject
    to change. Use them with caution. If you currently do not have developer
    preview access, please contact help@twilio.com. """

    def __init__(self, version, payload, subscription_sid, type=None):
        """
        Initialize the SubscribedEventInstance

        :returns: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        """
        super(SubscribedEventInstance, self).__init__(version)

        # Marshaled Properties
        self._properties = {
            'account_sid': payload.get('account_sid'),
            'type': payload.get('type'),
            'version': deserialize.integer(payload.get('version')),
            'subscription_sid': payload.get('subscription_sid'),
            'url': payload.get('url'),
        }

        # Context
        self._context = None
        self._solution = {'subscription_sid': subscription_sid, 'type': type or self._properties['type'], }

    @property
    def _proxy(self):
        """
        Generate an instance context for the instance, the context is capable of
        performing various actions.  All instance actions are proxied to the context

        :returns: SubscribedEventContext for this SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventContext
        """
        if self._context is None:
            self._context = SubscribedEventContext(
                self._version,
                subscription_sid=self._solution['subscription_sid'],
                type=self._solution['type'],
            )
        return self._context

    @property
    def account_sid(self):
        """
        :returns: The account_sid
        :rtype: unicode
        """
        return self._properties['account_sid']

    @property
    def type(self):
        """
        :returns: The type
        :rtype: unicode
        """
        return self._properties['type']

    @property
    def version(self):
        """
        :returns: The version
        :rtype: unicode
        """
        return self._properties['version']

    @property
    def subscription_sid(self):
        """
        :returns: The subscription_sid
        :rtype: unicode
        """
        return self._properties['subscription_sid']

    @property
    def url(self):
        """
        :returns: The url
        :rtype: unicode
        """
        return self._properties['url']

    def update(self, version):
        """
        Update the SubscribedEventInstance

        :param unicode version: The version

        :returns: The updated SubscribedEventInstance
        :rtype: twilio.rest.events.v1.subscription.subscribed_event.SubscribedEventInstance
        """
        return self._proxy.update(version, )

    def delete(self):
        """
        Deletes the SubscribedEventInstance

        :returns: True if delete succeeds, False otherwise
        :rtype: bool
        """
        return self._proxy.delete()

    def __repr__(self):
        """
        Provide a friendly representation

        :returns: Machine friendly representation
        :rtype: str
        """
        context = ' '.join('{}={}'.format(k, v) for k, v in self._solution.items())
        return '<Twilio.Events.V1.SubscribedEventInstance {}>'.format(context)
