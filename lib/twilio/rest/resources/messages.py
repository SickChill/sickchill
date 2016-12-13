from . import InstanceResource, ListResource
from .media import MediaList
from .util import normalize_dates, parse_date


class Message(InstanceResource):
    """ A Message instance.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account that sent or received this message.

    .. attribute:: from

        The phone number that initiated this message in E.164 format. For
        incoming messages, this will be the remote phone. For outgoing
        messages, this will be one of your Twilio phone numbers.

    .. attribute:: to

        The phone number that received the message in E.164 format. For
        incoming messages, this will be one of your Twilio phone numbers.
        For outgoing messages, this will be the remote phone.

    .. attribute:: date_created

        The date that this resource was created, given in RFC 2822 format.

    .. attribute:: date_updated

        The date that this resource was last updated, given in RFC 2822 format.

    .. attribute:: date_sent

        The date that the SMS was sent, given in RFC 2822 format.

    .. attribute:: body

        The text body of the message, as a unicode string.

    .. attribute:: num_segments

        The number of SMS messages used to deliver the
        body specified.

    .. attribute:: num_media

        The number of media that are associated with the message. If num_media
        is 0, then the media and image subresource will not contain any images.

    .. attribute:: status

        The status of this message. Either queued, sending, sent,failed,
        or received.

    .. attribute:: direction

        The direction of this message. inbound for incoming messages,
        outbound-api for messages initiated via the REST API, outbound-call
        for messages initiated during a call or outbound-reply for messages
        initiated in response to an incoming message.

    .. attribute:: price

        The amount billed for the message, in the currency associated with
        the account.

    .. attribute:: price_unit

        The currency in which price is measured, in ISO 4127 format
        (e.g. USD,EUR, JPY).

    .. attribute:: api_version

        The version of the Twilio API used to process the message.

    .. attribute:: uri

        The URI for this resource, relative to https://api.twilio.com

    """

    subresources = [MediaList]

    def delete(self):
        """Delete this Message record from Twilio."""
        return self.parent.delete(self.sid)

    def redact(self):
        """Redact this Message's `body` field from Twilio while preserving
        the record itself and related metadata.
        """
        return self.parent.redact(self.sid)


class Messages(ListResource):
    name = "Messages"
    key = "messages"
    instance = Message

    def create(self, from_=None, **kwargs):
        """
        Create and send a Message.

        :param str to: The destination phone number.
        :param str `from_`: The phone number sending this message
            (must be a verified Twilio number)
        :param str body: The message you want to send,
            limited to 1600 characters.
        :param list media_url: A list of URLs of images to include in the
            message.
        :param status_callback: A URL that Twilio will POST to when
            your message is processed.
        :param str application_sid: The 34 character sid of the application
            Twilio should use to handle this message.
        """
        kwargs["from"] = from_
        return self.create_instance(kwargs)

    @normalize_dates
    def list(self, from_=None, before=None, after=None, date_sent=None, **kw):
        """
        Returns a page of :class:`Message` resources as a list. For
        paging information see :class:`ListResource`.

        :param to: Only show messages to this phone number.
        :param from_: Only show messages from this phone number.
        :param date after: Only list messages sent after this date.
        :param date before: Only list message sent before this date.
        :param date date_sent: Only list message sent on this date.
        :param `from_`: Only show messages from this phone number.
        :param date after: Only list messages logged after this datetime
        :param date before: Only list messages logged before this datetime
        """
        kw["From"] = from_
        kw["DateSent<"] = before
        kw["DateSent>"] = after
        kw["DateSent"] = parse_date(date_sent)
        return self.get_instances(kw)

    @normalize_dates
    def iter(self, from_=None, to=None, before=None, after=None,
             date_sent=None, **kwargs):
        """
        Returns an iterator of :class:`Message` resources.

        :param date after: Only list calls started after this datetime
        :param date before: Only list calls started before this datetime
        """
        kwargs["From"] = from_
        kwargs["To"] = to
        kwargs["DateSent<"] = before
        kwargs["DateSent>"] = after
        kwargs["DateSent"] = parse_date(date_sent)
        return super(Messages, self).iter(**kwargs)

    def update(self, sid, **kwargs):
        """ Updates the message for the given sid
        :param sid: The sid of the message to update.
        """
        return self.update_instance(sid, kwargs)

    def delete(self, sid):
        """Delete the specified Message record from Twilio."""
        return self.delete_instance(sid)

    def redact(self, sid):
        """Redact the specified Message record's Body field."""
        return self.update_instance(sid, {'Body': ''})
