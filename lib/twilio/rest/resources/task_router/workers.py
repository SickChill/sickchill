from .. import NextGenInstanceResource, NextGenListResource
from .statistics import Statistics
from .reservations import Reservations


class Worker(NextGenInstanceResource):
    """
    A Worker resource.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/workers>_`
    for more information.

    .. attribute:: sid

        The unique ID of this Worker.

    .. attribute:: account_sid

        The unique ID of the account that owns this worker.

    .. attribute:: workspace_sid

        The unique ID of the :class:`Workspace` that contains this worker.

    .. attribute:: friendly_name

        A human-readable name for this worker.

    .. attribute:: attributes

        A JSON object describing this worker. For example, for a Worker that
        handles English language phone calls:
            '{"language":"english","task-type":"phone"}'
        These attributes determine which :class:`TaskQueue` this worker will
        subscribe to. These attributes will also be passed to the Assignment
        Callback URL whenever TaskRouter assigns a :class:`Task` to this
        worker, so you can also use this as a place to store information that
        you'll need when routing a Task to the Worker (for example, the
        Worker's phone number or Twilio Client name).

    .. attribute:: available

        A Boolean value indicating whether the worker can be assigned another
        task. When true, the worker can be assigned a new task; when false,
        the worker will not be assigned any tasks.

    .. attribute:: activity_sid

        The unique ID of the :class:`Activity` this Worker is currently
        performing.

    .. attribute:: activity_name

        A string describing the worker's current activity. Workers may only
        perform Activities that exist in this Workspace.

    .. attribute:: date_created

        The time this worker was created, given in UTC ISO 8601 format.

    .. attribute:: date_updated

        The time this worker was last updated, given in UTC ISO 8601 format.

    .. attribute:: date_status_changed

        The time of the last change to this worker's activity. Used to
        calculate :class: `Workflow` statistics.
    """
    subresources = [
        Statistics,
        Reservations
    ]

    def delete(self):
        """
        Delete a worker.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update a worker.
        """
        return self.parent.update_instance(self.name, kwargs)


class Workers(NextGenListResource):
    """ A list of Worker resources """

    name = "Workers"
    instance = Worker

    def __init__(self, base_uri, auth, timeout, **kwargs):
        super(Workers, self).__init__(base_uri, auth, timeout, **kwargs)
        self.statistics = Statistics(self.uri, auth, timeout, **kwargs)

    def create(self, friendly_name, **kwargs):
        """
        Create a Workflow.

        :param friendly_name: String representing user-friendly name for the
            Worker.
        :param activity_sid: A valid Activity describing the worker's initial
            state.
        :param attributes: JSON object describing this worker. For example:
            { 'email: 'Bob@foo.com', 'phone': '8675309' }. This data will be
            passed to the Assignment Callback URL whenever Work Distribution
            Service assigns a Task to this worker.
        """
        kwargs['friendly_name'] = friendly_name
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete the given worker
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Worker` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)
