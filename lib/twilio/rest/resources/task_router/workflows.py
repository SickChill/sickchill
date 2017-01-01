from .. import NextGenInstanceResource, NextGenListResource
from .statistics import Statistics


class Workflow(NextGenInstanceResource):
    """
    A Workflow resource.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/workflows>_`
    for more information.

    .. attribute:: sid

        The unique ID of the Workflow.

    .. attribute:: account_sid

        The ID of the account that owns this Workflow.

    .. attribute:: workspace_sid

        The ID of the :class:`Workspace` that contains this Workflow.

    .. attribute:: friendly_name

        A human-readable description of this Workflow.

    .. attribute:: assignment_callback_url

        The URL that will be called whenever a :class:`Task` managed by this
        Workflow is assigned to a :class:`Worker`.

    .. attribute:: fallback_assignment_callback_url

        If the request to the `assignment_callback_url` fails, the assignment
        callback will be made to this URL.

    .. attribute:: configuration

        A JSON document configuring the rules for this workflow.

    .. attribute:: task_reservation_timeout

        Determines how long TaskRouter will wait for a confirmation response
        from your application after assigning a Task to a worker. Defaults to
        120 seconds.

    .. attribute:: date_created

        The time this workflow was created, as UTC in ISO 8601 format.

    .. attribute:: date_updated

        The time this workflow was last updated, as UTC in ISO 8601 format.
    """
    subresources = [
        Statistics,
    ]

    def delete(self):
        """
        Delete a workflow.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update a workflow.
        """
        return self.parent.update_instance(self.name, kwargs)


class Workflows(NextGenListResource):
    """ A list of Workflow resources """

    name = "Workflows"
    instance = Workflow

    def create(self, friendly_name, configuration, assignment_callback_url,
               **kwargs):
        """
        Create a Workflow.

        :param friendly_name: A string representing a human readable name for
            this Workflow. Examples include 'Inbound Call Workflow' or '2014
            Outbound Campaign'.
        :param configuration: JSON document configuring the rules for this
            Workflow.
        :param assignment_callback_url: A valid URL for the application that
            will process task assignment events.
        :param fallback_assignment_callback_url: If the request to the
            assignment_callback_url fails, the assignment callback will be made
            to this URL.
        :param task_reservation_timeout: An integer value controlling how long
            in seconds Work Distribution Service will wait for a confirmation
            response from your application after assigning a Task to a worker.
            Defaults to 120 seconds.
        """
        kwargs['friendly_name'] = friendly_name
        kwargs['configuration'] = configuration
        kwargs['assignment_callback_url'] = assignment_callback_url
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete the given workflow
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Workflow` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
