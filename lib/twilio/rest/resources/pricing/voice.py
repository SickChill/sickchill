from .. import NextGenInstanceResource, NextGenListResource


class Voice(object):
    """Holds references to the Voice pricing resources."""

    name = "Voice"
    key = "voice"

    def __init__(self, base_uri, auth, timeout):
        self.uri = "%s/Voice" % base_uri
        self.countries = VoiceCountries(self.uri, auth, timeout)
        self.numbers = VoiceNumbers(self.uri, auth, timeout)


class VoiceCountry(NextGenInstanceResource):
    """Pricing information for Twilio Voice services in a specific country.

    .. attribute:: country

        The full name of the country.

    .. attribute:: iso_country

        The country's 2-character ISO code.

    .. attribute:: price_unit

        The currency in which prices are measured, in ISO 4127 format
        (e.g. 'usd', 'eur', 'jpy').

    .. attribute:: outbound_prefix_prices

        A list of dicts containing pricing information as follows:
            - prefix_list: a list of number prefixes in the requested country
              that have the same pricing
            - friendly_name: a descriptive name for this prefix set
            - call_base_price: the base price per minute for calls to numbers
              matching any of these prefixes
            - call_current_price: the current price per minute (including
              volume discounts, etc.) for your account to make calls to
              numbers matching these prefixes

    .. attribute:: inbound_call_prices

        A list of dicts containing pricing information for inbound calls:
            - number_type: 'local', 'mobile', 'national', or 'toll_free'
            - call_base_price: the base price per minute to receive a call
              to this number type
            - call_current_price: the current price per minute (including
              volume discounts, etc.) for your account to receive a call
              to this number type
    """

    id_key = "iso_country"


class VoiceCountries(NextGenListResource):

    instance = VoiceCountry
    key = "countries"
    name = "Countries"

    def get(self, iso_country):
        """Retrieve pricing information for Twilio Voice in the specified
        country.

        :param iso_country: The two-letter ISO code for the country
        """
        return self.get_instance(iso_country)

    def list(self):
        """Retrieve the list of countries in which Twilio Voice is
        available."""
        resp, page = self.request("GET", self.uri)

        return [self.load_instance(i) for i in page[self.key]]


class VoiceNumber(NextGenInstanceResource):
    """Pricing information for Twilio Voice services to and from a given
    phone number.

    .. attribute:: phone_number

        The E.164-formatted phone number this pricing information applies to

    .. attribute:: country

        The name of the country this phone number belongs to

    .. attribute:: iso_country

        The two-character ISO code for the country

    .. attribute:: outbound_call_price

        A dict containing pricing information for outbound calls to this
        number:
            - base_price: the base price per minute for a call to this number
            - current_price: the current price per minute (including discounts,
            etc.) for a call to this number

    .. attribute:: inbound_call_price

        A dict containing pricing information for inbound call to this number,
        or null if this number is not Twilio-hosted.

            - number_type: "local", "mobile", "national", or "toll_free"
            - call_base_price: the base price per minute to receive a call to
            this number
            - call_current_price: the current price per minute (including
            discounts, etc.) to receive a call to this number
    """

    id_key = "number"


class VoiceNumbers(NextGenListResource):

    instance = VoiceNumber
    key = "numbers"
    name = "Numbers"

    def get(self, phone_number):
        """ Retrieve pricing information for a specific phone number.
        :param phone_number: the E.164-formatted number to retrieve info for
        :return: a :class:`VoiceNumber` instance
        """

        return self.get_instance(phone_number)
