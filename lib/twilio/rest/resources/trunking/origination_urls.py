from .. import NextGenInstanceResource, NextGenListResource


class OriginationUrl(NextGenInstanceResource):
    """
    An Origination URL resource.
    See the `TaskRouter API reference
    <https://www.twilio.com/docs/sip-trunking/rest/origination-urls>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Origination URL.

    .. attribute:: trunk_sid

        The unique ID of the Trunk that owns this Credential List.
    """

    def delete(self):
        """
        Delete an Origination URL.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Update an Origination URL.
        """
        return self.parent.update_instance(self.name, kwargs)


class OriginationUrls(NextGenListResource):
    """ A list of Origination URL resources """

    name = "OriginationUrls"
    instance = OriginationUrl
    key = "origination_urls"

    def create(self, friendly_name, sip_url, priority, weight, enabled):
        """
        Create a Origination URL.

        :param friendly_name: A human readable descriptive text, up to 64
            characters long.
        :param sip_url: The SIP address you want Twilio to route your
            Origination calls to. This must be a sip: schema.
        :param priority: Priority ranks the importance of the URI. Value
            ranges from 0 - 65535.
        :param weight: Weight is used to determine the share of load when
            more than one URI has the same priority.
            Value ranges from 0 - 65535.
        :param enabled: A boolean value indicating whether the URL is
            enabled or disabled.

        """
        data = {
            'friendly_name': friendly_name,
            'sip_url': sip_url,
            'priority': priority,
            'weight': weight,
            'enabled': enabled
        }
        return self.create_instance(data)

    def list(self, **kwargs):
        """
        Retrieve the list of Origination URL resources for a given trunk sid.
        :param Page: The subset of results that needs to be fetched
        :param PageSize: The size of the Page that needs to be fetched
        """
        return super(OriginationUrls, self).list(**kwargs)

    def update(self, origination_url_sid, data):
        """
        Update an Origination Url.

        :param origination_url_sid: A human readable Origination Url sid.
        :param data: Attributes that needs to be updated.
        """
        return self.update_instance(origination_url_sid, data)

    def delete(self, origination_url_sid):
        """
        Delete an Origination Url.

        :param origination_url_sid: A human readable Origination Url sid.
        """
        return self.delete_instance(origination_url_sid)
