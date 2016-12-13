from . import InstanceResource, ListResource


class Application(InstanceResource):
    """ An application resource """

    def update(self, **kwargs):
        """
        Update this application
        """
        return self.parent.update(self.name, **kwargs)

    def delete(self):
        """
        Delete this application
        """
        return self.parent.delete(self.name)


class Applications(ListResource):

    name = "Applications"
    instance = Application

    def list(self, **kwargs):
        """
        Returns a page of :class:`Application` resources as a list. For paging
        information see :class:`ListResource`

        :param date friendly_name: List applications with this friendly name
        """
        return self.get_instances(kwargs)

    def create(self, **kwargs):
        """
        Create an :class:`Application` with any of these optional parameters.

        :param friendly_name: A human readable description of the application,
                              with maximum length 64 characters.
        :param api_version: Requests to this application's URLs will start a
                            new TwiML session with this API version.
                            Either 2010-04-01 or 2008-08-01.
        :param voice_url: The URL that Twilio should request when somebody
                          dials a phone number assigned to this application.
        :param voice_method: The HTTP method that should be used to request the
                             VoiceUrl. Either GET or POST.
        :param voice_fallback_url: A URL that Twilio will request if an error
                                   occurs requesting or executing the TwiML
                                   defined by VoiceUrl.
        :param voice_fallback_method: The HTTP method that should be used to
                                      request the VoiceFallbackUrl. Either GET
                                      or POST.
        :param status_callback: The URL that Twilio will request to pass status
                                parameters (such as call ended) to your
                                application.
        :param status_callback_method: The HTTP method Twilio will use to make
                                       requests to the StatusCallback URL.
                                       Either GET or POST.
        :param voice_caller_id_lookup: Do a lookup of a caller's name from the
                                       CNAM database and post it to your app.
                                       Either true or false.
        :param sms_url: The URL that Twilio should request when somebody sends
                        an SMS to a phone number assigned to this application.
        :param sms_method: The HTTP method that should be used to request the
                           SmsUrl. Either GET or POST.
        :param sms_fallback_url: A URL that Twilio will request if an error
                                 occurs requesting or executing the TwiML
                                 defined by SmsUrl.
        :param sms_fallback_method: The HTTP method that should be used to
                                    request the SmsFallbackUrl. Either GET
                                    or POST.
        :param sms_status_callback: Twilio will make a POST request to this URL
                                    to pass status parameters (such as sent or
                                    failed) to your application if you specify
                                    this application's Sid as the
                                    ApplicationSid on an outgoing SMS request.
        """
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        """
        Update an :class:`Application` with the given parameters.

        All the parameters are describe above in :meth:`create`
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """
        Delete an :class:`Application`
        """
        return self.delete_instance(sid)
