import re

from twilio.exceptions import TwilioException
from .util import change_dict_key, transform_params
from .util import UNSET_TIMEOUT
from . import InstanceResource, ListResource


TYPES = {"local": "Local", "tollfree": "TollFree", "mobile": "Mobile"}


class AvailablePhoneNumber(InstanceResource):
    """ An available phone number resource

   .. attribute:: friendly_name

      A nicely-formatted version of the phone number.

   .. attribute:: phone_number

      The phone number, in E.164 (i.e. "+1") format.

   .. attribute:: lata

      The LATA of this phone number.

   .. attribute:: rate_center

      The rate center of this phone number.

   .. attribute:: latitude

      The latitude coordinate of this phone number.

   .. attribute:: longitude

      The longitude coordinate of this phone number.

   .. attribute:: region

      The two-letter state or province abbreviation of this phone number.

   .. attribute:: postal_code

      The postal (zip) code of this phone number.

   .. attribute:: iso_country

        The country for this number

   .. attribute:: address_requirements

        Whether the phone number requires you or your customer to have an
        Address registered with Twilio. Possible values are 'none', 'any',
        'local', or 'foreign'.

   .. attribute:: beta

        (boolean) Phone numbers new to the Twilio platform are marked as beta.

    """

    def __init__(self, parent):
        # Available Phone Numbers have no sid.
        super(AvailablePhoneNumber, self).__init__(parent, "")
        self.name = ""

    def purchase(self, **kwargs):
        return self.parent.purchase(phone_number=self.phone_number,
                                    **kwargs)


class AvailablePhoneNumbers(ListResource):

    name = "AvailablePhoneNumbers"
    key = "available_phone_numbers"
    instance = AvailablePhoneNumber

    def __init__(self, base_uri, auth, timeout, phone_numbers):
        super(AvailablePhoneNumbers, self).__init__(base_uri, auth, timeout)
        self.phone_numbers = phone_numbers

    def get(self, sid):
        raise TwilioException("Individual AvailablePhoneNumbers have no sid")

    def list(self, type="local", country="US", region=None, postal_code=None,
             lata=None, rate_center=None, **kwargs):
        """
        Search for phone numbers
        """
        kwargs["in_region"] = kwargs.get("in_region", region)
        kwargs["in_postal_code"] = kwargs.get("in_postal_code", postal_code)
        kwargs["in_lata"] = kwargs.get("in_lata", lata)
        kwargs["in_rate_center"] = kwargs.get("in_rate_center", rate_center)
        params = transform_params(kwargs)

        uri = "%s/%s/%s" % (self.uri, country, TYPES[type])
        resp, page = self.request("GET", uri, params=params)

        return [self.load_instance(i) for i in page[self.key]]

    def load_instance(self, data):
        instance = self.instance(self.phone_numbers)
        instance.load(data)
        instance.load_subresources()
        return instance


class PhoneNumber(InstanceResource):
    """ An IncomingPhoneNumber object

   .. attribute:: sid

      A 34 character string that uniquely identifies this resource.

   .. attribute:: date_created

      The date that this resource was created, given as GMT RFC 2822 format.

   .. attribute:: date_updated

      The date that this resource was last updated, in GMT RFC 2822 format.

   .. attribute:: friendly_name

      A human readable descriptive text for this resource, up to 64 characters
      long. By default, the FriendlyName is a nicely formatted version of
      the phone number.

   .. attribute:: account_sid

      The unique id of the Account responsible for this phone number.

   .. attribute:: phone_number

      The incoming phone number. e.g., +16175551212 (E.164 format)

   .. attribute:: api_version

      Calls to this phone number will start a new TwiML session with this
      API version.

   .. attribute:: voice_caller_id_lookup

      Look up the caller's caller-ID name from the CNAM database (additional
      charges apply). Either true or false.

   .. attribute:: voice_url

      The URL Twilio will request when this phone number receives a call.

   .. attribute:: voice_method

      The HTTP method Twilio will use when requesting the above Url.
      Either GET or POST.

   .. attribute:: voice_fallback_url

      The URL that Twilio will request if an error occurs retrieving or
      executing the TwiML requested by Url.

   .. attribute:: voice_fallback_method

      The HTTP method Twilio will use when requesting the VoiceFallbackUrl.
      Either GET or POST.

   .. attribute:: status_callback

      The URL that Twilio will request to pass status parameters (such as
      call ended) to your application.

   .. attribute:: status_callback_method

      The HTTP method Twilio will use to make requests to the
      StatusCallback URL. Either GET or POST.

   .. attribute:: sms_url

      The URL Twilio will request when receiving an incoming SMS message
      to this number.

   .. attribute:: sms_method

      The HTTP method Twilio will use when making requests to the SmsUrl.
      Either GET or POST.

   .. attribute:: sms_fallback_url

      The URL that Twilio will request if an error occurs retrieving or
      executing the TwiML from SmsUrl.

   .. attribute:: sms_fallback_method

      The HTTP method Twilio will use when requesting the above URL.
      Either GET or POST.

   .. attribute:: uri

      The URI for this resource, relative to https://api.twilio.com.

   .. attribute:: beta

      (boolean) Phone numbers new to the Twilio platform are marked as beta.
    """

    def load(self, entries):
        """ Set the proper Account owner of this phone number """

        # Only check if entries has a uri
        if "account_sid" in entries:
            # Parse the parent's uri to get the scheme and base
            uri = re.sub(r'AC(.*)', entries["account_sid"],
                         self.parent.base_uri)

            self.parent = PhoneNumbers(
                uri,
                self.parent.auth,
                self.parent.timeout
            )
            self.base_uri = self.parent.uri

        super(PhoneNumber, self).load(entries)

    def transfer(self, account_sid):
        """
        Transfer the phone number with sid from the current account to another
        identified by account_sid
        """
        a = self.parent.transfer(self.name, account_sid)
        self.load(a.__dict__)

    def update(self, **kwargs):
        """
        Update this phone number instance.
        """
        kwargs_copy = dict(kwargs)
        change_dict_key(kwargs_copy, from_key="status_callback_url",
                        to_key="status_callback")

        a = self.parent.update(self.name, **kwargs_copy)
        self.load(a.__dict__)

    def delete(self):
        """
        Release this phone number from your account. Twilio will no longer
        answer calls to this number, and you will stop being billed the monthly
        phone number fees. The phone number will eventually be recycled and
        potentially given to another customer, so use with care. If you make a
        mistake, contact us... we may be able to give you the number back.
        """
        return self.parent.delete(self.name)


class PhoneNumbers(ListResource):

    name = "IncomingPhoneNumbers"
    key = "incoming_phone_numbers"
    instance = PhoneNumber

    def __init__(self, base_uri, auth, timeout=UNSET_TIMEOUT):
        super(PhoneNumbers, self).__init__(base_uri, auth, timeout)
        self.available_phone_numbers = \
            AvailablePhoneNumbers(base_uri, auth, timeout, self)

    def delete(self, sid):
        """
        Release this phone number from your account. Twilio will no longer
        answer calls to this number, and you will stop being billed the
        monthly phone number fees. The phone number will eventually be
        recycled and potentially given to another customer, so use with care.
        If you make a mistake, contact us... we may be able to give you the
        number back.
        """
        return self.delete_instance(sid)

    def list(self, type=None, **kwargs):
        """
        :param phone_number: Show phone numbers that match this pattern.
        :param friendly_name: Show phone numbers with this friendly name
        :param type: Filter numbers by type. Available types are
            'local', 'mobile', or 'tollfree'

        You can specify partial numbers and use '*' as a wildcard.
        """

        uri = self.uri
        if type:
            uri = "%s/%s" % (self.uri, TYPES[type])

        params = transform_params(kwargs)
        resp, page = self.request("GET", uri, params=params)

        return [self.load_instance(i) for i in page[self.key]]

    def purchase(self, status_callback_url=None, **kwargs):
        """
        Attempt to purchase the specified number. The only required parameters
        are **either** phone_number or area_code

        :returns: Returns a :class:`PhoneNumber` instance on success,
                  :data:`False` on failure
        :raises: A :exc:`TypeError` if neither phone_number or area_code
        is specified.
        """
        kwargs["StatusCallback"] = kwargs.get("status_callback",
                                              status_callback_url)

        if 'phone_number' not in kwargs and 'area_code' not in kwargs:
            raise TypeError("phone_number or area_code is required")

        number_type = kwargs.pop('type', False)
        uri = self.uri
        if number_type:
            uri = "%s/%s" % (self.uri, TYPES[number_type])

        params = transform_params(kwargs)
        resp, instance = self.request('POST', uri, data=params)

        return self.load_instance(instance)

    def search(self, **kwargs):
        """
        :param type: The type of phone number to search for.
        :param str country: Only show numbers for this country (iso2)
        :param str region: When searching the US, show numbers in this state
        :param str postal_code: Only show numbers in this area code
        :param str rate_center: US only.
        :param str near_lat_long: Find close numbers within Distance miles.
            Should be string of format "{lat},{long}"
        :param integer distance: Search radius for a Near- query in miles.
        :param boolean beta: Whether to include numbers new to the Twilio
            platform.
        """
        return self.available_phone_numbers.list(**kwargs)

    def transfer(self, sid, account_sid):
        """
        Transfer the phone number with sid from the current account to another
        identified by account_sid
        """
        return self.update(sid, account_sid=account_sid)

    def update(self, sid, **kwargs):
        """
        Update this phone number instance
        """
        kwargs_copy = dict(kwargs)
        change_dict_key(kwargs_copy, from_key="status_callback_url",
                        to_key="status_callback")

        if "application_sid" in kwargs_copy:
            for sid_type in ["voice_application_sid", "sms_application_sid"]:
                if sid_type not in kwargs_copy:
                    kwargs_copy[sid_type] = kwargs_copy["application_sid"]
            del kwargs_copy["application_sid"]
        return self.update_instance(sid, kwargs_copy)
