from .util import transform_params
from . import InstanceResource, ListResource


class Sandbox(InstanceResource):

    id_key = "pin"

    def update(self, **kwargs):
        """
        Update your Twilio Sandbox
        """
        a = self.parent.update(**kwargs)
        self.load(a.__dict__)


class Sandboxes(ListResource):

    name = "Sandbox"
    instance = Sandbox

    def get(self):
        """Request the specified instance resource"""
        return self.get_instance(self.uri)

    def update(self, **kwargs):
        """
        Update your Twilio Sandbox
        """
        resp, entry = self.request("POST", self.uri,
                                   body=transform_params(kwargs))
        return self.create_instance(entry)
