from .. import InstanceResource, ListResource


class IpAddress(InstanceResource):
    """ An IP address entry in an Access Control List.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this IpAddress.

    .. attribute:: friendly_name

        A human-readable name for this IP address.

    .. attribute:: ip_address

        The IP address in dotted-decimal IPv4 notation.

    .. attribute:: date_created

        The date that this resource was created.

    .. attribute:: date_updated

        The date that this resource was last updated.

    """

    def update(self, **kwargs):
        """Update this address."""
        return self.parent.update_instance(self.name, **kwargs)

    def delete(self):
        """
        Delete this address.
        """
        return self.parent.delete_instance(self.name)


class IpAddresses(ListResource):
    name = "IpAddresses"
    key = "ip_addresses"
    instance = IpAddress

    def create(self, friendly_name, ip_address, **kwargs):
        """Add an IP address to a SipIpAccessControlList.

        :param str friendly_name: A human-readable name for this address.
        :param str ip_address: A dotted-decimal IPv4 address
        """
        kwargs['friendly_name'] = friendly_name
        kwargs['ip_address'] = ip_address
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """Update an :class:`IpAddress`.

        :param sid: String identifier for an address
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """Remove an :class:`IpAddress` from a :class:`SipIpAccessControlList`.

        :param sid: String identifier for an address
        """
        return self.delete_instance(sid)


class SipIpAccessControlList(InstanceResource):
    """ A list of IP addresses for controlling access to a SIP Domain.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this ACL.

    .. attribute:: friendly_name

        A human-readable name for this SipIpAccessControlList.

    .. attribute:: date_created

        The date that this resource was created.

    .. attribute:: date_updated

        The date that this resource was last updated.

    """
    subresources = [IpAddresses]

    def update(self, **kwargs):
        """Update this address."""
        return self.parent.update_instance(self.name, **kwargs)

    def delete(self):
        """
        Delete this address.
        """
        return self.parent.delete_instance(self.name)


class SipIpAccessControlLists(ListResource):
    name = "IpAccessControlLists"
    key = "ip_access_control_lists"
    instance = SipIpAccessControlList

    def create(self, friendly_name, **kwargs):
        """ Create a :class:`SipIpAccessControlList`.

        :param str friendly_name: A human-readable name for this ACL.
        """
        kwargs['friendly_name'] = friendly_name
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """ Change the name of a :class:`SipIpAccessControlList`.

        :param str sid: String identifier for a SipIpAccessControlList resource

        :param str friendly_name: A human-readable name for the ACL.
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`SipIpAccessControlList`.

        :param sid: String identifier for a SipIpAccessControlList resource
        """
        return self.delete_instance(sid)
