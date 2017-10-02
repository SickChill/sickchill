from .. import NextGenInstanceResource, NextGenListResource


class Reservation(NextGenInstanceResource):
    """
    A Reservation resource.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/tasks#reservation>_`
    for more information.

    .. attribute:: sid

        The unique ID of this Reservation.

    .. attribute:: account_Sid

        The unique ID of the Account that owns this :class:`Task`.

    .. attribute:: workspace_sid

        The unique ID of the :class:`Workspace` that contains this
        :class:`Task`.

    .. attribute:: task_sid

        The unique ID of the reserved :class:`Task`.

    .. attribute:: worker_sid

        The unique ID of the reserved :class:`Worker`.

    .. attribute:: worker_name

        Human-readable description of the reserved Worker.

    .. attribute:: reservation_status

        The current status of the reservation. One of 'pending',
        'accepted', 'rejected', or 'timeout'.
    """

    def update(self, **kwargs):
        """
        Update a reservation.

        :param reservation_status: Either accepted or rejected. Specifying
            accepted means the Worker has received the Task and will process
            it. Work Distribution Service will no longer consider this task
            eligible for assignment, and no other Worker will receive this
            Task. Specifying rejected means the Worker has refused the
            assignment and Work Distribution Service will attempt to assign
            this Task to the next eligible Worker.
        :param worker_activity_sid: If rejecting a reservation, change the
            worker that is tied to this reservation to the supplied activity.
            If not provided, the WorkerPreviousActivitySid on the Reservation
            will be used.
        """
        return self.parent.update_instance(self.name, kwargs)


class Reservations(NextGenListResource):
    """ A list of Reservation resources """

    name = "Reservations"
    instance = Reservation

    def update(self, sid, **kwargs):
        """
        Update a :class:`Reservation` with the given parameters.

        :param sid: Reservation sid to update.
        :param reservation_status: Either accepted or rejected. Specifying
            accepted means the Worker has received the Task and will process
            it. Work Distribution Service will no longer consider this task
            eligible for assignment, and no other Worker will receive this
            Task. Specifying rejected means the Worker has refused the
            assignment and Work Distribution Service will attempt to assign
            this Task to the next eligible Worker.
        :param worker_activity_sid: If rejecting a reservation, change the
            worker that is tied to this reservation to the supplied activity.
            If not provided, the WorkerPreviousActivitySid on the Reservation
            will be used.
        """
        return self.update_instance(sid, kwargs)
