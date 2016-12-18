from twilio.rest.resources import (
    NextGenInstanceResource,
    NextGenListResource,
    transform_params,
)


class PhoneNumber(NextGenInstanceResource):
    """
    Represents information about a phone number.

    .. attribute:: phone_number

        The phone number in normalized E.164 format, e.g. "+14158675309"

    .. attribute:: national_format

        The phone number in localized format, e.g. "(415) 867-5309"

    .. attribute:: country_code

        The ISO 3166-1 two-letter code for this phone number's country, e.g.
        "US" for United States

    .. attribute:: carrier

        A dictionary of information about the carrier responsible for this
        number, if requested.

        Contains the following:
            - mobile_country_code: the country code of the mobile carrier.
            Only populated if the number is a mobile number.
            - mobile_network_code: the network code of the mobile carrier.
            Only populated if the number is a mobile number.
            - name: the name of the carrier.
            - type: the type of the number ("mobile", "landline", or "voip")
            - error_code: the error code of the carrier info request, if one
            occurred
    """
    id_key = "phone_number"


class PhoneNumbers(NextGenListResource):
    name = "PhoneNumbers"
    instance = PhoneNumber

    def get(self, number, include_carrier_info=False, country_code=None):
        """Look up a phone number.

        :param str number: The phone number to query.
        :param bool include_carrier_info: Whether to do a carrier lookup on
            the phone number. See twilio.com for the latest pricing.
        :param str country_code: If the number is provided in a local format
        rather than E.164, specify the two-letter code of the country to parse
        the number for.
        """

        params = {}
        if country_code is not None:
            params['country_code'] = country_code

        if include_carrier_info:
            params['type'] = 'carrier'

        params = transform_params(params)
        uri = "%s/%s" % (self.uri, number)
        _, item = self.request("GET", uri, params=params)

        return self.load_instance(item)
