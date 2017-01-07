from . import transform_params
from . import InstanceResource, ListResource


class CallerId(InstanceResource):

    def delete(self):
        """
        Deletes this caller ID from the account.
        """
        return self.delete_instance()

    def update(self, **kwargs):
        """
        Update the CallerId
        """
        self.update_instance(**kwargs)


class CallerIds(ListResource):
    """ A list of :class:`CallerId` resources """

    name = "OutgoingCallerIds"
    key = "outgoing_caller_ids"
    instance = CallerId

    def delete(self, sid):
        """
        Deletes a specific :class:`CallerId` from the account.
        """
        self.delete_instance(sid)

    def list(self, **kwargs):
        """
        :param phone_number: Show caller ids with this phone number.
        :param friendly_name: Show caller ids with this friendly name.
        """
        return self.get_instances(kwargs)

    def update(self, sid, **kwargs):
        """
        Update a specific :class:`CallerId`
        """
        return self.update_instance(sid, kwargs)

    def validate(self, phone_number, **kwargs):
        """
        Begin the validation process for the given number.

        Returns a dictionary with the following keys

        **account_sid**:
        The unique id of the Account to which the Validation Request belongs.

        **phone_number**: The incoming phone number being validated,
        formatted with a '+' and country code e.g., +16175551212

        **friendly_name**: The friendly name you provided, if any.

        **validation_code**: The 6 digit validation code that must be entered
        via the phone to validate this phone number for Caller ID.

        :param phone_number: The phone number to call and validate
        :param friendly_name: A description for the new caller ID
        :param call_delay: Number of seconds to delay the validation call.
        :param extension: Digits to dial after connecting the validation call.
        :returns: A response dictionary
        """
        kwargs["phone_number"] = phone_number
        params = transform_params(kwargs)
        resp, validation = self.request("POST", self.uri, data=params)
        return validation
