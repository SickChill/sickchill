from . import InstanceResource, ListResource
from six import iteritems


class ConnectApp(InstanceResource):
    """ An authorized connect app """
    pass


class ConnectApps(ListResource):
    """ A list of Connect App resources """

    name = "ConnectApps"
    instance = ConnectApp
    key = "connect_apps"

    def list(self, **kwargs):
        """
        Returns a page of :class:`ConnectApp` resources as a list. For paging
        informtion see :class:`ListResource`
        """
        return self.get_instances(kwargs)


class AuthorizedConnectApp(ConnectApp):
    """ An authorized connect app """

    id_key = "connect_app_sid"

    def load(self, entries):
        """ Translate certain parameters into others"""
        result = {}

        for k, v in iteritems(entries):
            k = k.replace("connect_app_", "")
            result[k] = v

        super(AuthorizedConnectApp, self).load(result)


class AuthorizedConnectApps(ConnectApps):
    """ A list of Authorized Connect App resources """

    name = "AuthorizedConnectApps"
    instance = AuthorizedConnectApp
    key = "authorized_connect_apps"
