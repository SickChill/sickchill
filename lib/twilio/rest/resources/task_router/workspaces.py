from .. import NextGenInstanceResource, NextGenListResource
from .statistics import Statistics


class Workspace(NextGenInstanceResource):
    """
    A Workspace resource.
    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/workspaces>_`
    for more information.

    .. attribute:: sid

        The unique ID of the Workspace

    .. attribute:: account_sid

        The ID of the account that owns this Workspace

    .. attribute:: friendly_name

        Human readable description of this workspace (for example "Sales Call
        Center" or "Customer Support Team")

    .. attribute:: default_activity_sid

        The ID of the default :class:`Activity` that will be used when new
        Workers are created in this Workspace.

    .. attribute:: default_activity_name

        The human readable name of the default activity. Read only.

    .. attribute:: timeout_activity_sid

        The ID of the Activity that will be assigned to a Worker when a
        :class:`Task` reservation times out without a response.

    .. attribute:: timeout_activity_name

        The human readable name of the timeout activity. Read only.

    .. attribute:: event_callback_url

        An optional URL where the Workspace will publish events. You can use
        this to gather data for reporting.

    .. attribute:: date_created

        The time the Workspace was created, given as UTC in ISO 8601 format.

    .. attribute:: date_updated

        The time the Workspace was last updated, given as UTC in ISO 8601
        format.
    """
    subresources = [
        Statistics,
    ]

    def delete(self):
        """
        Delete a workspace.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update a workspace.
        """
        return self.parent.update_instance(self.name, kwargs)


class Workspaces(NextGenListResource):
    """ A list of Workspace resources """

    name = "Workspaces"
    instance = Workspace

    def create(self, friendly_name, **kwargs):
        """
        Create a Workspace.

        :param friendly_name: Human readable description of this workspace (for
            example "Customer Support" or "2014 Election Campaign").
        :param event_callback_url: If provided, the Workspace will publish
            events to this URL. You can use this to gather data for reporting.
            See Workspace Events for more information.
        :param template: One of the available template names. Will
            pre-configure this Workspace with the Workflow and Activities
            specified in the template. Currently "FIFO" is the only available
            template, which will configure Work Distribution Service with a set
            of default activities and a single queue for first-in, first-out
            distribution.
        """
        kwargs['friendly_name'] = friendly_name
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete the given workspace
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Workspace` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
