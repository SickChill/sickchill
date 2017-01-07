from .. import NextGenInstanceResource, NextGenListResource


class PhoneNumber(NextGenInstanceResource):
    """
    A Phone Number resource.
    See the `TaskRouter API reference
    <https://www.twilio.com/docs/sip-trunking/rest/phone-numbers>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Phone Number.

    .. attribute:: trunk_sid

        The unique ID of the Trunk that owns this Phone Number.
    """

    def delete(self):
        """
        Removes an associated Phone Number from a Trunk.
        """
        return self.parent.delete_instance(self.name)


class PhoneNumbers(NextGenListResource):
    """ A list of Phone Numbers resources """

    name = "PhoneNumbers"
    instance = PhoneNumber
    key = "phone_numbers"

    def list(self, **kwargs):
        """
        Retrieves the list of Phone Number resources for a given trunk sid.
        :param Page: The subset of results that needs to be fetched
        :param PageSize: The size of the Page that needs to be fetched
        """
        return super(PhoneNumbers, self).list(**kwargs)

    def create(self, phone_number_sid):
        """
        Associates a Phone Number with the given Trunk.

        :param phone_number_sid:
        Associates a Phone Number with the given trunk.
        """
        data = {
            'phone_number_sid': phone_number_sid
        }
        return self.create_instance(data)

    def delete(self, sid):
        """
        Disassociates a phone number from the trunk.
        :param sid: Phone Number Sid
        """
        return self.delete_instance(sid)
