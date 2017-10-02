from twilio.rest.resources.base import InstanceResource, ListResource


class Key(InstanceResource):
    """
    A key resource.
    See https://www.twilio.com/docs/api/rest-keys

    .. attribute:: sid

        The unique ID for this key.

    .. attribute:: friendly_name

        A human-readable description of this key.

    .. attribute:: secret

        This key's secret.

    .. attribute:: date_created

        The date this key was created, given as UTC in ISO 8601 format.

    .. attribute:: date_updated

        The date this singing key was last updated, given as UTC in ISO 8601
        format.
    """

    def update(self, **kwargs):
        """
        Update this key
        """
        return self.parent.update(self.name, **kwargs)

    def delete(self):
        """
        Delete this key
        """
        return self.parent.delete(self.name)


class Keys(ListResource):
    name = "Keys"
    key = "keys"
    instance = Key

    def create(self, **kwargs):
        """
        Create a :class:`Key` with any of these optional parameters.

        :param friendly_name: A human readable description of the signing key.
        """
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Key` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`Key`
        """
        return self.delete_instance(sid)

    def list(self, **kwargs):
        """
        Returns a page of :class:`Key` resources as a list
        """
        return self.get_instances(kwargs)
