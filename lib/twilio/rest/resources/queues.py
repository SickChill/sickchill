from . import InstanceResource, ListResource


class Member(InstanceResource):
    """ A Member of a queue

   .. attribute:: call_sid

      A 34 character string that uniquely identifies the call that is enqueued.

   .. attribute:: date_enqueued

      The date that the member was enqueued, given in RFC 2822 format.

   .. attribute:: wait_time

      The number of seconds the member has been in the queue.

   .. attribute:: position

      This member's current position in the queue.

   .. attribute:: uri

      The URI for this resource, relative to https://api.twilio.com.
    """

    id_key = "call_sid"


class Members(ListResource):
    """ A list of :class:`Member` objects """
    name = "Members"
    instance = Member
    key = "queue_members"

    def list(self, **kwargs):
        """
        Returns a list of :class:`Member` resources in the given queue

        :param queue_sid: :class:`Queue` this participant is part of
        """
        return self.get_instances(kwargs)

    def dequeue(self, url, call_sid='Front', **kwargs):
        """
        Dequeues a member from the queue and have the member's call
        begin executing the TwiML document at the url.

        :param call_sid: Call sid specifying the member, if not given,
                         the member at the front of the queue will be used
        :param url: url of the TwiML document to be executed.
        """
        kwargs['url'] = url
        return self.update_instance(call_sid, kwargs)


class Queue(InstanceResource):
    """ An instance of a Queue

   .. attribute:: sid

      A 34 character string that uniquely identifies this queue.

   .. attribute:: friendly_name

      A user-provided string that identifies this queue.

   .. attribute:: current_size

      The count of calls currently in the queue.

   .. attribute:: max_size

      The upper limit of calls allowed to be in the queue.
      `unlimited` is an option. The default is 100.

   .. attribute:: average_wait_time

      The average wait time of the members of this queue in seconds.
      This is calculated at the time of the request.

   .. attribute:: uri

      The URI for this resource, relative to https://api.twilio.com.

   .. attribute:: queue_members

      A :class:`Members` object holding the :class:`Member` objects in this
      queue.
    """

    subresources = [
        Members
    ]

    def update(self, **kwargs):
        """
        Update this queue

        :param friendly_name: A new friendly name for this queue
        :param max_size: A new max size. Changing a max size to less than the
                         current size results in the queue rejecting incoming
                         requests until it shrinks below the new max size
        """
        return self.parent.update_instance(self.name, kwargs)

    def delete(self):
        """
        Delete this queue.  Can only be run on empty queues.
        """
        return self.parent.delete_instance(self.name)


class Queues(ListResource):
    name = "Queues"
    instance = Queue

    def list(self, **kwargs):
        """
        Returns a page of :class:`Queue` resources as a list sorted
        by DateUpdated. For paging informtion see :class:`ListResource`
        """
        return self.get_instances(kwargs)

    def create(self, name, **kwargs):
        """ Create an :class:`Queue` with any of these optional parameters.

        :param name: A human readable description of the application,
                              with maximum length 64 characters.
        :param max_size: The limit on calls allowed into the queue (optional)
        """
        kwargs['friendly_name'] = name
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Queue`

        :param sid: String identifier for a Queue resource
        :param friendly_name: A new friendly name for this queue
        :param max_size: A new max size. Changing a max size to less than the
                         current size results in the queue rejecting incoming
                         requests until it shrinks below the new max size
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`Queue`. Can only be run on empty queues.

        :param sid: String identifier for a Queue resource
        """
        return self.delete_instance(sid)
