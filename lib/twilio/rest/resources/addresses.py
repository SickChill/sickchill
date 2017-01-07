from twilio.exceptions import TwilioException
from twilio.rest.resources import InstanceResource, ListResource


class DependentPhoneNumber(InstanceResource):
    """A purchased phone number that depends on a particular
    :class:`Address`.

    Attributes are the same as :class:`PhoneNumber`.

    DependentPhoneNumbers are a read-only resource and cannot
    be updated or deleted.
    """
    pass


class DependentPhoneNumbers(ListResource):
    """A list of purchased phone numbers that depend on a particular
    :class:`Address`.

    Included numbers are those that require an
    address on file and have no other candidate addresses of the appropriate
    type (local, foreign) associated with the owning account.

    If this list has entries for a given Address, that address cannot be
    deleted until the numbers are released from your account or alternate
    addresses are provided to satisfy the requirements.

    This resource is read-only and cannot be updated or deleted, but will
    reflect the current state of the owning account's addresses (i.e. if
    you add another address that satisfies a number's requirements, it will
    not appear in subsequent requests to this list resource).
    """
    name = "DependentPhoneNumbers"
    key = "dependent_phone_numbers"
    instance = DependentPhoneNumber


class Address(InstanceResource):
    """An Address resource. See https://www.twilio.com/docs/api/rest/address

    .. attribute:: friendly_name

        A human-readable description of this address. Maximum 64 characters.

    .. attribute:: customer_name

        Your or your customer's name or business name.

    .. attribute:: street

        The number and street address where you or your customer are located.

    .. attribute:: city

        The city in which you or your customer are located.

    .. attribute:: region

        The state or region in which you or your customer are located.

    .. attribute:: postal_code

        The postal code in which you or your customer are located.

    .. attribute:: iso_country

        The ISO country code of your or your customer's address.
    """
    subresources = [DependentPhoneNumbers]

    def update(self, **kwargs):
        """Update this phone number instance.

        Parameters are as described in :meth:`Addresses.create`, with
        the exception that `iso_country` cannot be updated on an existing
        Address (create a new one instead).
        """
        return self.parent.update(self.sid, kwargs)


class Addresses(ListResource):
    name = "Addresses"
    key = "addresses"
    instance = Address

    def list(self, customer_name=None, friendly_name=None, iso_country=None):
        kwargs = {
            'customer_name': customer_name,
            'friendly_name': friendly_name,
            'iso_country': iso_country,
        }
        return self.get_instances(kwargs)

    def create(self, customer_name, street, city, region, postal_code,
               iso_country, friendly_name=None):
        """Create an :class:`Address`.

        :param str customer_name: Your customer's name
        :param str street: The number and street of your address
        :param str city: The city of you or your customer's address
        :param str region: The region or state
        :param str postal_code: The postal code of your address
        :param str iso_country: The ISO 3166-1 alpha-2 (two-character)
            country code, e.g. 'US' or 'AU'
        :param str friendly_name: A user-defined name for this address
            (optional; up to 64 characters)
        """
        kwargs = {
            'customer_name': customer_name,
            'street': street,
            'city': city,
            'region': region,
            'postal_code': postal_code,
            'iso_country': iso_country,
        }

        if friendly_name is not None:
            kwargs['friendly_name'] = friendly_name

        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """Update an :class:`Address` with the given parameters.

        Parameters are described above in :meth:`create`, with
        the exception that `iso_country` cannot be updated on
        an existing Address (create a new one instead).
        """
        if 'iso_country' in kwargs:
            raise TwilioException(
                "Cannot update iso_country on an existing Address",
            )

        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """Delete an :class:`Address`.

        :param str sid: The sid of the Address to delete.
        """
        return self.delete_instance(sid)
