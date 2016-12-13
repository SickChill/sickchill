from .. import NextGenInstanceResource, NextGenListResource


class MessagingCountry(NextGenInstanceResource):
    """Pricing information for Twilio Messages in a specific country.

    .. attribute:: iso_country

        The country's 2-character ISO 3166-1 code.

    """
    id_key = "iso_country"


class MessagingCountries(NextGenListResource):
    """A list of countries where Twilio Messages are available.

    The returned list of MessagingCountry objects will not have pricing
    information populated. To get pricing information for a specific country,
    retrieve it with the :meth:`get` method.
    """

    instance = MessagingCountry
    key = "countries"
    name = "Countries"

    def get(self, iso_country):
        """Retrieve pricing information for Twilio Messages in the specified
        country.

        :param iso_country: The two-letter ISO code for the country
        """
        return self.get_instance(iso_country)

    def list(self, **kwargs):
        """Retrieve the list of countries in which Twilio Messages are
        available."""

        return super(MessagingCountries, self).list(**kwargs)
