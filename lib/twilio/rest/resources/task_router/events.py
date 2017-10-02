from twilio.rest.resources.base import (
    NextGenInstanceResource,
    NextGenListResource,
)


class Event(NextGenInstanceResource):
    """An Event resource representing a state change in a TaskRouter
    Workspace.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/events>_`
    for more information.

    .. attribute:: event_type

        An identifier for this event.

    .. attribute:: account_sid

        The unique ID of the Account that owns this Event.

    .. attribute:: description

        A description of the event.

    .. attribute:: resource_type

        The type of object this event is most relevant to (:class:`Task`,
        :class:`Reservation`, :class:`Worker`).

    .. attribute:: resource_sid

        The unique ID of the object this event is most relevant to.

    .. attribute:: event_date

        The time this event was sent, in UTC ISO 8601 format.

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

        :param minutes: (Optional, Default=15) Definition of the interval in
            minutes prior to now.
        :param start_date: (Optional, Default=15 minutes prior) Filter events
            by a start date.
        :param end_date: (Optional, Default=Now) Filter events by an end date.
        :param resource_sid: (Optional) Sid of the event resource.
        :param event_type: (Optional) The type of event to filter by.
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
