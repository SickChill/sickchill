from .. import NextGenInstanceResource, NextGenListResource


class IpAccessControlList(NextGenInstanceResource):
    """
    An IP Access Control List Resource.
    See the `SIP Trunking API reference
    <https://www.twilio.com/docs/sip-trunking/rest/ip-access-control-lists>_`
    for more information.

    .. attribute:: sid

        The unique ID for this IP Access Control List.

    .. attribute:: trunk_sid

        The unique ID of the Trunk that owns this Credential List.
    """

    def delete(self):
        """
        Disassociate an Ip Access Control List.
        """
        return self.parent.delete_instance(self.name)


class IpAccessControlLists(NextGenListResource):
    """ A list of IP Access Control List resources """

    name = "IpAccessControlLists"
    instance = IpAccessControlList
    key = "ip_access_control_lists"

    def list(self, **kwargs):
        """
        Retrieve the IP Access Control List resources.
        :param Page: The subset of results that needs to be fetched
        :param PageSize: The size of the Page that needs to be fetched
        """
        return super(IpAccessControlLists, self).list(**kwargs)

    def create(self, ip_access_control_list_sid):
        """
        Associate an IP Access Control List with a Trunk.

        :param ip_access_control_list_sid:
            A human readable IP Access Control list sid.
        """
        data = {
            'ip_access_control_list_sid': ip_access_control_list_sid
        }
        return self.create_instance(data)

    def delete(self, ip_access_control_list_sid):
        """
        Disassociate an Ip Access Control List from the Trunk.

        :param ip_access_control_list_sid:
            A human readable IP Access Control list sid.
        """
        return self.delete_instance(ip_access_control_list_sid)
