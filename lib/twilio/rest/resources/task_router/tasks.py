from .. import NextGenInstanceResource, NextGenListResource


class Task(NextGenInstanceResource):
    """
    A Task resource.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/tasks>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Task.

    .. attribute:: account_sid

        The ID of the account that owns this Task.

    .. attribute:: workspace_sid

        The ID of the :class:`Workspace` that contains this Task.

    .. attribute:: workflow_sid

        The ID of the :class:`Workflow` that is responsible for routing
        this Task.

    .. attribute:: attributes

        The user-defined JSON string describing the custom attributes of
        this work.

    .. attribute:: age

        The number of seconds since this Task was created.

    .. attribute:: priority

        The current priority score of the task, as assigned by the Workflow.
        Tasks with higher values will be assigned before tasks with lower
        values.

    .. attribute:: task_queue_sid

        The ID of the current TaskQueue this task occupies, controlled by the
        Workflow.

    .. attribute:: assignment_status

        A string representing the assignment state of the task. May be
        'pending', 'reserved', 'assigned', or 'canceled'.

    .. attribute:: reason

        The reason the task was canceled (if applicable).

    .. attribute:: date_created

        The date this task was created, as UTC in ISO 8601 format.

    .. attribute:: date_updated

        The date this task was last updated, as UTC in ISO 8601 format.
    """

    def delete(self):
        """
        Delete a task.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update a task.
        """
        return self.parent.update_instance(self.name, kwargs)


class Tasks(NextGenListResource):
    """ A list of Task resources """

    name = "Tasks"
    instance = Task

    def create(self, attributes, workflow_sid, **kwargs):
        """
        Create a Task.

        :param attributes: Url-encoded JSON string describing the attributes of
            this task. This data will be passed back to the Workflow's
            AssignmentCallbackURL when the Task is assigned to a Worker. An
            example task: { 'task_type': 'call', 'twilio_call_sid': '...',
            'customer_ticket_number': '12345' }.
        :param workflow_sid: The workflow_sid for the Workflow that you would
            like to handle routing for this Task.
        :param timeout: If provided, time-to-live for the task in seconds,
            before it is automatically canceled
        """
        kwargs['attributes'] = attributes
        kwargs['workflow_sid'] = workflow_sid
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete the given task
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Task` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
