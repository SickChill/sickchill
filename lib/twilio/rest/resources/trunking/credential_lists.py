from .. import NextGenInstanceResource, NextGenListResource


class CredentialList(NextGenInstanceResource):
    """
    A Credential List Resource.
    See the `SIP Trunking API reference
    <https://www.twilio.com/docs/sip-trunking/rest/credential-lists>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Credential List.

    .. attribute:: trunk_sid

        The unique ID of the Trunk that owns this Credential List.
    """

    def delete(self):
        """
        Disassociates a Credential List from the trunk.
        """
        return self.parent.delete_instance(self.name)


class CredentialLists(NextGenListResource):
    """ A list of Credential List resources """

    name = "CredentialLists"
    instance = CredentialList
    key = "credential_lists"

    def list(self, **kwargs):
        """
        Retrieve the list of Credential List resources for a given trunk sid.
        :param Page: The subset of results that needs to be fetched
        :param PageSize: The size of the Page that needs to be fetched
        """
        return super(CredentialLists, self).list(**kwargs)

    def create(self, credential_list_sid):
        """
        Associate a Credential List with a Trunk.

        :param credential_list_sid: A human readable Credential list sid.
        """
        data = {
            'credential_list_sid': credential_list_sid
        }
        return self.create_instance(data)

    def delete(self, credential_list_sid):
        """
        Disassociates a Credential List from the Trunk.

        :param credential_list_sid: A human readable Credential list sid.
        """
        return self.delete_instance(credential_list_sid)
