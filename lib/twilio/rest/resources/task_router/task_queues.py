from .. import NextGenInstanceResource, NextGenListResource
from .statistics import Statistics


class TaskQueue(NextGenInstanceResource):
    """
    A TaskQueue resource.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/taskqueues>_`
    for more information.

    .. attribute:: sid

        The unique ID of this TaskQueue.

    .. attribute:: account_sid

        The unique ID of the account that owns this TaskQueue.

    .. attribute:: workspace_sid

        The unique ID of the :class:`Workspace` that contains this TaskQueue.

    .. attribute:: friendly_name

        Human-readable description of this TaskQueue (e.g. "Customer Support"
        or "Sales").

    .. attribute:: target_workers

        The worker selection expressions associated with this TaskQueue.

    .. attribute:: reservation_activity_sid

        The :class:`Activity` to assign a :class:`Worker` when they are
        reserved for a :class:`Task` from this TaskQueue. Defaults to
        'Reserved for Task'.

    .. attribute:: assignment_activity_sid

        The Activity to assign a Worker when they accept a Task from this
        Taskqueue. Defaults to 'Unavailable for Assignment'.
    """
    subresources = [
        Statistics,
    ]

    def delete(self):
        """
        Delete a task queue.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update a task queue.
        """
        return self.parent.update_instance(self.name, kwargs)


class TaskQueues(NextGenListResource):
    """ A list of TaskQueue resources """

    name = "TaskQueues"
    instance = TaskQueue
    key = "task_queues"

    def __init__(self, base_uri, auth, timeout, **kwargs):
        super(TaskQueues, self).__init__(base_uri, auth, timeout, **kwargs)
        self.statistics = Statistics(self.uri, auth, **kwargs)

    def create(self, friendly_name, assignment_activity_sid,
               reservation_activity_sid, **kwargs):
        """
        Create a TaskQueue.

        :param friendly_name: Human readable description of this TaskQueue (for
            example "Support - Tier 1", "Sales" or "Escalation")
        :param assignment_activity_sid: ActivitySID to assign workers once a
            task is assigned for them.
        :param reservation_activity_sid: ActivitySID to assign workers once a
            task is reserved for them.
        """
        kwargs['friendly_name'] = friendly_name
        kwargs['assignment_activity_sid'] = assignment_activity_sid
        kwargs['reservation_activity_sid'] = reservation_activity_sid
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete the given task queue
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update a :class:`TaskQueue` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
