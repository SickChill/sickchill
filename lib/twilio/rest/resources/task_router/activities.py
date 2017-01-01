from .. import NextGenInstanceResource, NextGenListResource


class Activity(NextGenInstanceResource):
    """
    An Activity resource.
    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/activities>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Activity.

    .. attribute:: account_sid

        The unique ID of the Account that owns this Activity.

    .. attribute:: workspace_sid

        The unique ID of the :class:`Workspace` that owns this Activity.

    .. attribute:: friendly_name

        A human-readable name for the Activity, such as 'on-call', 'break',
        'email', etc. These names will be used to calculate and expose
        statistics about workers, and give you visibility into the state of
        each of your workers.

    .. attribute:: available

        Boolean value indicating whether the worker should be eligible to
        receive a Task when they occupy this Activity. For example, in an
        activity called 'On Call', the worker would be unavailable to receive
        additional Task assignments.

    .. attribute:: date_created

        The date this Activity was created, given as UTC in ISO 8601 format.

    .. attribute:: date_updated

        The date this Activity was last updated, given as UTC in ISO 8601
        format.
    """

    def delete(self):
        """
        Delete an activity.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update an activity.
        """
        return self.parent.update_instance(self.name, kwargs)


class Activities(NextGenListResource):
    """ A list of Activity resources """

    name = "Activities"
    instance = Activity

    def create(self, friendly_name, available):
        """
        Create an Activity.

        :param friendly_name: A human-readable name for the activity, such as
            'On Call', 'Break', 'Email', etc. Must be unique in this Workspace.
            These names will be used to calculate and expose statistics about
            workers, and give you visibility into the state of each of your
            workers.
        :param available: Boolean value indicating whether the worker should be
            eligible to receive a Task when they occupy this Activity. For
            example, a call center might have an activity named 'On Call' with
            an availability set to 'false'.
        """
        return self.create_instance({'friendly_name': friendly_name,
                                     'available': available})

    def delete(self, sid):
        """
        Delete the given activity
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update an :class:`Activity` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
