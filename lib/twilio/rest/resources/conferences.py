from .util import parse_date, normalize_dates
from . import InstanceResource, ListResource


class Participant(InstanceResource):

    id_key = "call_sid"

    def mute(self):
        """
        Mute the participant
        """
        self.update_instance(muted="true")

    def unmute(self):
        """
        Unmute the participant
        """
        self.update_instance(muted="false")

    def kick(self):
        """
        Remove the participant from the given conference
        """
        self.delete_instance()


class Participants(ListResource):

    name = "Participants"
    instance = Participant

    def list(self, **kwargs):
        """
        Returns a list of :class:`Participant` resources in the given
        conference

        :param conference_sid: Conference this participant is part of
        :param boolean muted: If True, only show participants who are muted
        """
        return self.get_instances(kwargs)

    def mute(self, call_sid):
        """
        Mute the given participant
        """
        return self.update(call_sid, muted=True)

    def unmute(self, call_sid):
        """
        Unmute the given participant
        """
        return self.update(call_sid, muted=False)

    def kick(self, call_sid):
        """
        Remove the participant from the given conference
        """
        return self.delete(call_sid)

    def delete(self, call_sid):
        """
        Remove the participant from the given conference
        """
        return self.delete_instance(call_sid)

    def update(self, sid, **kwargs):
        """
        :param sid: Participant identifier
        :param boolean muted: If true, mute this participant
        """
        return self.update_instance(sid, kwargs)


class Conference(InstanceResource):

    subresources = [
        Participants
    ]


class Conferences(ListResource):

    name = "Conferences"
    instance = Conference

    @normalize_dates
    def list(self, updated_before=None, updated_after=None, created_after=None,
             created_before=None, updated=None, created=None, **kwargs):
        """
        Return a list of :class:`Conference` resources

        :param status: Show conferences with this status
        :param friendly_name: Show conferences with this exact friendly_name
        :param date updated_after: List conferences updated after this date
        :param date updated_before: List conferences updated before this date
        :param date created_after: List conferences created after this date
        :param date created_before: List conferences created before this date
        """
        kwargs["DateUpdated"] = parse_date(kwargs.get("date_updated", updated))
        kwargs["DateCreated"] = parse_date(kwargs.get("date_created", created))
        kwargs["DateUpdated<"] = updated_before
        kwargs["DateUpdated>"] = updated_after
        kwargs["DateCreated<"] = created_before
        kwargs["DateCreated>"] = created_after
        return self.get_instances(kwargs)
