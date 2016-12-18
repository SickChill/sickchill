from .util import normalize_dates
from . import InstanceResource, ListResource


class Notification(InstanceResource):

    def delete(self):
        """
        Delete this notification
        """
        return self.delete_instance()


class Notifications(ListResource):

    name = "Notifications"
    instance = Notification

    @normalize_dates
    def list(self, before=None, after=None, **kwargs):
        """
        Returns a page of :class:`Notification` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in a
        notification, the full HTTP request and response data is only returned
        in the Notification instance resource representation.

        :param date after: Only list notifications logged after this datetime
        :param date before: Only list notifications logger before this datetime
        :param log_level: If 1, only shows errors. If 0, only show warnings
        """
        kwargs["MessageDate<"] = before
        kwargs["MessageDate>"] = after
        return self.get_instances(kwargs)

    def delete(self, sid):
        """
        Delete a given Notificiation
        """
        return self.delete_instance(sid)
