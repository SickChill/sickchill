from .members import Members
from .messages import Messages
from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class Channel(NextGenInstanceResource):

    subresources = [
        Members,
        Messages
    ]

    def update(self, **kwargs):
        """
        Updates the Channel instance
        :param sid: Channel instance identifier
        :param type: Channel type
        :param friendly_name: Channel's friendly name
        :param unique_name: Channel's Unique name
        :param attributes: Additional attributes that needs to be stored with
        channel
        :return: the updated instance
        """
        return self.update_instance(**kwargs)

    def delete(self):
        """
        Delete this channel
        """
        return self.delete_instance()


class Channels(NextGenListResource):

    name = "Channels"
    instance = Channel

    def list(self, **kwargs):
        """
        Returns a page of :class:`Channel` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the Channel instance resource representation.
        """
        return self.get_instances(kwargs)

    def create(self, **kwargs):
        """
        Create a channel.

        :param str friendly_name: Channel's friendly name
        :param unique_name: Channel's Unique name
        :param str attributes: Developer-specific data (json) storage

        :return: A :class:`Channel` object
        """
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete a given Channel
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Updates the Channel instance identified by sid
        :param sid: Channel instance identifier
        :param type: Channel type
        :param friendly_name: Channel's friendly name
        :param unique_name: Channel's Unique name
        :param attributes: Additional attributes that needs to be stored with
        channel
        :return: Updated instance
        """
        return self.update_instance(sid, kwargs)
