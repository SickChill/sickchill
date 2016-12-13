from . import InstanceResource, ListResource
from .util import normalize_dates, parse_date


class Media(InstanceResource):
    """ Represents media associated with a :class:`Message`.

    .. attribute:: sid

        A 34 character string that uniquely identifies this resource.

    .. attribute:: account_sid

        The unique id of the Account responsible for this media.

    .. attribute:: date_created

        The date that this resource was created, given in RFC 2822 format.

    .. attribute:: date_updated

        The date that this resource was last updated, given in RFC 2822 format.

    .. attribute:: parent_sid

        The MessageSid of the message that created the media.

    .. attribute:: content_type

        The default content-type of the media, for example image/jpeg,
        image/png, or image/gif.

    .. attribute:: uri

        The URI for this resource, relative to https://api.twilio.com

    """

    def delete(self):
        """
        Delete this media.
        """
        return self.parent.delete_instance(self.name)


class MediaList(ListResource):
    name = "Media"
    key = "media_list"
    instance = Media

    def __call__(self, message_sid):
        # `Media` is a word of ambiguous plurality. This causes issues.
        # To match the rest of the library:
        # `client.media` needs to return a new MediaList.
        # `client.media('message_sid')` needs to return a MediaList
        # for a given message.

        base_uri = "%s/Messages/%s" % (self.base_uri, message_sid)
        return MediaList(base_uri, self.auth, self.timeout)

    def __init__(self, *args, **kwargs):
        super(MediaList, self).__init__(*args, **kwargs)

    @normalize_dates
    def list(self, before=None, after=None, date_created=None, **kw):
        """
        Returns a page of :class:`Media` resources as a list. For
        paging information see :class:`ListResource`.

        :param date after: Only list media created after this date.
        :param date before: Only list media created before this date.
        :param date date_created: Only list media created on this date.
        :param sid message_sid: Only list media created by the given MessageSid
        """
        kw["DateCreated<"] = before
        kw["DateCreated>"] = after
        kw["DateCreated"] = parse_date(date_created)
        return self.get_instances(kw)

    def delete(self, sid):
        """
        Delete a :class:`Media`.

        :param sid: String identifier for a Media resource
        """
        return self.delete_instance(sid)
