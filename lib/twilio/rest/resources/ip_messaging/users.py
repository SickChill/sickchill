from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class User(NextGenInstanceResource):

    def update(self, **kwargs):
        """
        Updates this User instance
        :param role_sid: The role to assign the user.
        :return: Updated instance
        """
        return self.update_instance(**kwargs)

    def delete(self):
        """
        Delete this user
        """
        return self.delete_instance()


class Users(NextGenListResource):

    name = "Users"
    instance = User

    def list(self, **kwargs):
        """
        Returns a page of :class:`User` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the User instance resource representation.

        """
        return self.get_instances(kwargs)

    def create(self, identity, **kwargs):
        """
        Creates a User

        :param str identity: The identity of the user.
        :param str role_sid: The role to assign the user.

        :return: A :class:`User` object
        """
        kwargs["identity"] = identity
        return self.create_instance(kwargs)

    def delete(self, sid):
        """
        Delete a given User
        """
        return self.delete_instance(sid)

    def update(self, sid, **kwargs):
        """
        Updates the User instance identified by sid
        :param sid: User instance identifier
        :param role_sid: The role to assign the user.
        :return: Updated instance
        """
        return self.update_instance(sid, kwargs)
