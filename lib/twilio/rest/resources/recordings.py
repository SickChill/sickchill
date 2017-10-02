from .util import normalize_dates

from .transcriptions import Transcriptions
from .base import InstanceResource, ListResource


class Recording(InstanceResource):

    subresources = [Transcriptions]

    def __init__(self, *args, **kwargs):
        super(Recording, self).__init__(*args, **kwargs)
        self.formats = {
            "mp3": self.uri + ".mp3",
            "wav": self.uri + ".wav",
        }

    def delete(self):
        """
        Delete this recording
        """
        return self.delete_instance()


class Recordings(ListResource):

    name = "Recordings"
    instance = Recording

    @normalize_dates
    def list(self, before=None, after=None, **kwargs):
        """
        Returns a page of :class:`Recording` resources as a list.
        For paging information see :class:`ListResource`.

        :param date after: Only list recordings logged after this datetime
        :param date before: Only list recordings logger before this datetime
        :param call_sid: Only list recordings from this :class:`Call`
        """
        kwargs["DateCreated<"] = before
        kwargs["DateCreated>"] = after
        return self.get_instances(kwargs)

    @normalize_dates
    def iter(self, before=None, after=None, **kwargs):
        """
        Returns an iterator of :class:`Recording` resources.

        :param date after: Only list recordings logged after this datetime
        :param date before: Only list recordings logger before this datetime
        """
        kwargs["DateCreated<"] = before
        kwargs["DateCreated>"] = after
        return super(Recordings, self).iter(**kwargs)

    def delete(self, sid):
        """
        Delete the given recording
        """
        return self.delete_instance(sid)
