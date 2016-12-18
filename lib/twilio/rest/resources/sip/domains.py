from .. import InstanceResource, ListResource


class IpAccessControlListMapping(InstanceResource):
    def delete(self):
        """
        Remove this mapping (disassociate the ACL from the Domain).
        """
        return self.parent.delete_instance(self.name)


class IpAccessControlListMappings(ListResource):
    name = "IpAccessControlListMappings"
    key = "ip_access_control_list_mappings"
    instance = IpAccessControlListMapping

    def create(self, ip_access_control_list_sid, **kwargs):
        """Add a :class:`CredentialListMapping` to this domain.

        :param sid: String identifier for an existing
                                    :class:`CredentialList`.
        """
        kwargs.update(ip_access_control_list_sid=ip_access_control_list_sid)
        return self.create_instance(kwargs)

    def delete(self, sid):
        """Remove a :class:`CredentialListMapping` from this domain.

        :param sid: String identifier for a CredentialList resource
        """
        return self.delete_instance(sid)


class CredentialListMapping(InstanceResource):
    def delete(self):
        """
        Remove this mapping (disassociate the CredentialList from the Domain).
        """
        return self.parent.delete_instance(self.name)


class CredentialListMappings(ListResource):
    name = "CredentialListMappings"
    key = "credential_list_mappings"
    instance = CredentialListMapping

    def create(self, credential_list_sid, **kwargs):
        """Add a :class:`CredentialListMapping` to this domain.

        :param sid: String identifier for an existing
                                    :class:`CredentialList`.
        """
        kwargs.update(credential_list_sid=credential_list_sid)
        return self.create_instance(kwargs)

    def delete(self, sid):
        """Remove a :class:`CredentialListMapping` from this domain.

        :param sid: String identifier for a CredentialList resource
        """
        return self.delete_instance(sid)


class Domain(InstanceResource):
    """An inbound SIP Domain.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this domain.

    .. attribute:: domain_name

        A unique domain name for this inbound SIP endpoint. Must end in
        .sip.twilio.com.

    .. attribute:: friendly_name

        A human-readable name for this SIP domain. (restrictions?)

    .. attribute:: auth_type

        ???

    .. attribute:: voice_url

        The URL Twilio will request when this domain receives a call.

    .. attribute:: voice_method

        The HTTP method Twilio will use when requesting the above voice_url.
        Either GET or POST.

    .. attribute:: voice_fallback_url

        The URL that Twilio will request if an error occurs retrieving or
        executing the TwiML requested by voice_url.

    .. attribute:: voice_fallback_method

        The HTTP method Twilio will use when requesting the voice_fallback_url.
        Either GET or POST.

    .. attribute:: voice_status_callback

        The URL that Twilio will request to pass status parameters (such as
        call ended) to your application.

    .. attribute:: voice_status_callback_method

        The HTTP method Twilio will use to make requests to the status_callback
        URL. Either GET or POST.

    .. attribute:: date_created

        The date that this resource was created.

    .. attribute:: date_updated

        The date that this resource was last updated.

    """
    subresources = [IpAccessControlListMappings, CredentialListMappings]

    def update(self, **kwargs):
        """
        Update this :class:`Domain`

        Available attributes to update are described above as instance
        attributes.
        """
        return self.parent.update_instance(self.name, kwargs)

    def delete(self):
        """
        Delete this domain.
        """
        return self.parent.delete_instance(self.name)


class Domains(ListResource):
    name = "Domains"
    key = "domains"
    instance = Domain

    def create(self, domain_name, **kwargs):
        """ Create a :class:`Domain`.

        :param str domain_name: A unique domain name ending in
        '.sip.twilio.com'
        :param str friendly_name: A human-readable name for this domain.
        :param str voice_url: The URL Twilio will request when this domain
        receives a call.
        :param voice_method: The HTTP method Twilio should use to request
            voice_url.
        :type voice_method: None (defaults to 'POST'), 'GET', or 'POST'
        :param str voice_fallback_url: A URL that Twilio will request if an
            error occurs requesting or executing the TwiML at voice_url
        :param str voice_fallback_method: The HTTP method that Twilio should
            use to request the fallback_url
        :type voice_fallback_method: None (defaults to 'POST'),
            'GET', or 'POST'
        :param str voice_status_callback: A URL that Twilio will request when
            the call ends to notify your app.
        :param str voice_status_method: The HTTP method Twilio should use when
            requesting the above URL.

        """
        kwargs['domain_name'] = domain_name
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """
        Update a :class:`Domain`

        Available attributes to update are described above in :meth:`create`.

        :param sid: String identifier for a Domain resource
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete a :class:`Domain`.

        :param sid: String identifier for a Domain resource
        """
        return self.delete_instance(sid)
