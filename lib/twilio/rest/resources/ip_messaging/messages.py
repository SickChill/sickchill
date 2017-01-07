from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class Message(NextGenInstanceResource):

    def update(self, **kwargs):
        """
        Updates the Message instance
        :param sid: Message instance identifier
        :param service_sid: Service instance identifier
        :param channel_sid: Channel instance identifier
        :param body: Message's body
        :return: the updated instance
        """
        return self.update_instance(**kwargs)

    def delete(self):
        """
        Delete this message
        """
        return self.delete_instance()


class Messages(NextGenListResource):

    name = "Messages"
    instance = Message

    def list(self, **kwargs):
        """
        Returns a page of :class:`Message` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the Message instance resource representation.

        """
        return self.get_instances(kwargs)

    def create(self, body, **kwargs):
        """
        Create a Message.

        :param str body: The body of the message.
        :param str from: The message author's identity.

        :return: A :class:`Message` object
        """
        kwargs["body"] = body
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete a given Message
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Updates the Message instance identified by sid
        :param sid: Message instance identifier
        :param service_sid: Service instance identifier
        :param channel_sid: Channel instance identifier
        :param body: Message's body
        :return: the updated instance
        """
        return self.update_instance(sid, kwargs)
