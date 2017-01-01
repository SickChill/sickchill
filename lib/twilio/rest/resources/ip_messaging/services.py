from .channels import Channels
from .roles import Roles
from .users import Users
from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class Service(NextGenInstanceResource):

    subresources = [
        Channels,
        Roles,
        Users
    ]

    def update(self, **kwargs):
        """
        Updates this Service instance
        :return: Updated instance
        """
        return self.update_instance(**kwargs)

    def delete(self):
        """
        Delete this service
        """
        return self.delete_instance()


class Services(NextGenListResource):

    name = "Services"
    instance = Service

    def list(self, **kwargs):
        """
        Returns a page of :class:`Service` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the Service instance resource representation.

        """
        return self.get_instances(kwargs)

    def create(self, friendly_name, **kwargs):
        """
        Create a service.

        :param str friendly_name: The friendly name for the service

        :return: A :class:`Service` object
        """
        kwargs["friendly_name"] = friendly_name
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete a given Service
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Updates the Service instance identified by sid
        :param sid: Service instance identifier
        :return: Updated instance
        """
        return self.update_instance(sid, kwargs)
