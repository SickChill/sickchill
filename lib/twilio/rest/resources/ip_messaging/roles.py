from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class Role(NextGenInstanceResource):

    def update(self, permission, **kwargs):
        """
        Updates this Role instance
        :param permission: Role permission
        :return: Updated instance
        """
        kwargs['permission'] = permission
        return self.update_instance(**kwargs)

    def delete(self):
        """
        Delete this role
        """
        return self.delete_instance()


class Roles(NextGenListResource):

    name = "Roles"
    instance = Role

    def list(self, **kwargs):
        """
        Returns a page of :class:`Role` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the Role instance resource representation.

        """
        return self.get_instances(kwargs)

    def delete(self, sid):
        """
        Delete a given Role
        """
        return self.delete_instance(sid)

    def create(self, friendly_name, role_type, permission):
        """
        Creates a Role
        :param str friendly_name: Human readable name to the Role
        :param str role_type: Type of role - deployment or channel
        :param str permission: Set of permissions for the role
        """
        kwargs = {
            "friendly_name": friendly_name,
            "type": role_type,
            "permission": permission
        }
        return self.create_instance(kwargs)

    def update(self, sid, permission, **kwargs):
        """
        Updates the Role instance identified by sid
        :param sid: Role instance identifier
        :param permission: Role permission
        :return: Updated instance
        """
        kwargs['permission'] = permission
        return self.update_instance(sid, kwargs)
