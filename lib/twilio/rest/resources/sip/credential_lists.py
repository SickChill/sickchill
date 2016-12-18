from .. import InstanceResource, ListResource


class Credential(InstanceResource):
    """ A username/password entry in a CredentialList.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this Credential.

    .. attribute:: friendly_name

        A human-readable name for this resource.

    .. attribute:: username

        The username for this credential

    .. attribute:: date_created

        The date that this resource was created.

    .. attribute:: date_updated

        The date that this resource was last updated.

    """
    def update(self, **kwargs):
        """Update this credential."""
        return self.parent.update_instance(self.name, **kwargs)

    def delete(self):
        """
        Delete this credential.
        """
        return self.parent.delete_instance(self.name)


class Credentials(ListResource):
    name = "Credentials"
    key = "credentials"
    instance = Credential

    def create(self, username, password, **kwargs):
        """Add a Credential to a SipCredentialList.

        :param username: The username to add
        :param password: The password for the user
        """
        kwargs.update(username=username, password=password)
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """Update a :class:`Credential`.

        :param sid: String identifier for a credential
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """Remove a username/password

        :param sid: String identifier for a credential
        """
        return self.delete_instance(sid)


class SipCredentialList(InstanceResource):
    """ A list of username/password credentials used to control access to
    Domains.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this CredentialList.

    .. attribute:: friendly_name

        A human-readable name for this CredentialList.

    .. attribute:: date_created

        The date that this resource was created.

    .. attribute:: date_updated

        The date that this resource was last updated.

    """

    subresources = [Credentials]

    def update(self, **kwargs):
        """Update this credential list."""
        return self.parent.update_instance(self.name, **kwargs)

    def delete(self):
        """
        Delete this credential list.
        """
        return self.parent.delete_instance(self.name)


class SipCredentialLists(ListResource):
    name = "CredentialLists"
    key = "credential_lists"
    instance = SipCredentialList

    def create(self, friendly_name, **kwargs):
        """ Create a :class:`SipCredentialList`.

        :param friendly_name: A human-readable name for this credential list.
        """
        kwargs['friendly_name'] = friendly_name
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """
        Update a :class:`SipCredentialList`

        :param sid: String identifier for a SipCredentialList resource
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`SipCredentialList`.

        :param sid: String identifier for a SipCredentialList resource
        """
        return self.delete_instance(sid)
