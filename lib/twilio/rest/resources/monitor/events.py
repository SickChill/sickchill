from twilio.rest.resources.base import (
    NextGenInstanceResource,
    NextGenListResource,
)


class Event(NextGenInstanceResource):
    """An Event resource representing a state change in the Twilio API.

    See the `Monitor API reference
    <https://www.twilio.com/docs/api/rest/monitor>_`
    for more information.

    .. attribute:: sid

        The unique ID for this event.

    .. attribute:: account_sid

        The unique ID of the Account that owns this Event.

    .. attribute:: actor_sid

        The unique ID of the actor of this event.

    .. attribute:: actor_type

        The type of actor of this event.

    .. attribute:: description

        A description of the event.

    .. attribute:: event_date

        The time this event was sent, in UTC ISO 8601 format.

    .. attribute:: event_type

        The type of this event.

    .. attribute:: resource_sid

        The unique ID of the object this event is most relevant to.

    .. attribute:: resource_type

        The type of object this event is most relevant to.

    .. attribute:: source

        The source of this event.

    .. attribute:: source_ip_address

        The source's IP address for this event.

    .. attribute:: event_data

        Data about this specific Event.
    """
    pass


class Events(NextGenListResource):
    name = "Events"
    instance = Event

    def list(self, **kwargs):
        """
        Returns a page of :class:`Event` resources as a list. For paging
            information see :class:`NextGenListResource`

        :param actor_sid: (Optional) Sid of the event actor.
        :param start_date: (Optional) Filter events
            by a start date.
        :param end_date: (Optional) Filter events by an end date.
        :param resource_sid: (Optional) Sid of the event resource.
        :param event_type: (Optional) The type of event to filter by.
        :param source_ip_address: (Optional) The IP address of the event's
            source.
        """
        return super(Events, self).list(**kwargs)

    def get_instances(self, params):
        """
        Query the list resource for a list of InstanceResources.
        Raises a :exc:`~twilio.TwilioRestException` if requesting a page of
        results that does not exist.

        :param dict params: List of URL parameters to be included in request
        :param str page_token: Token of the page of results to retrieve
        :param int page_size: The number of results to be returned.
        :returns: -- the list of resources
        """
        return super(Events, self).get_instances(params)
