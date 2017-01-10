from twilio.rest.resources import NextGenInstanceResource, NextGenListResource


class Alert(NextGenInstanceResource):

    def delete(self):
        """
        Delete this alert
        """
        return self.delete_instance()


class Alerts(NextGenListResource):

    name = "Alerts"
    instance = Alert

    def list(self, before=None, after=None, **kwargs):
        """
        Returns a page of :class:`Alert` resources as a list.
        For paging information see :class:`ListResource`.

        **NOTE**: Due to the potentially voluminous amount of data in an
        alert, the full HTTP request and response data is only returned
        in the Alert instance resource representation.

        :param date after: Only list alerts logged after this datetime
        :param date before: Only list alerts logger before this datetime
        :param log_level: If 'error', only shows errors. If 'warning',
         only show warnings
        """
        kwargs["MessageDate<"] = before
        kwargs["MessageDate>"] = after
        return self.get_instances(kwargs)

    def delete(self, sid):
        """
        Delete a given Alert
        """
        return self.delete_instance(sid)
