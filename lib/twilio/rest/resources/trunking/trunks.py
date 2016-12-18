from .. import NextGenInstanceResource, NextGenListResource


class Trunk(NextGenInstanceResource):
    """
    A Trunk resource.
    See the `TaskRouter API reference
    <https://www.twilio.com/docs/sip-trunking/rest/trunks>_`
    for more information.

    .. attribute:: sid

        The unique ID for this Trunk.
    """

    def delete(self):
        """
        Deletes a Trunk.
        """
        return self.parent.delete_instance(self.name)

    def update(self, **kwargs):
        """
        Updates a Trunk.

        """
        return self.parent.update_instance(self.name, **kwargs)


class Trunks(NextGenListResource):
    """ A list of Trunk resources """

    name = "Trunks"
    instance = Trunk
    key = "trunks"

    def list(self, **kwargs):
        """
        Retrieve the list of Trunk resources.

        :param Page: The subset of results that needs to be fetched
        :param PageSize: The size of the Page that needs to be fetched
        """
        return super(Trunks, self).list(**kwargs)

    def create(self, **kwargs):
        """
        Creates a Trunk.
        """
        return self.create_instance(kwargs)

    def update(self, sid, body):
        """
        Updates a Trunk.
        :param sid: A human readable 34 character unique identifier
        :param body: Request body
        """
        return self.update_instance(sid, body)

    def delete(self, sid):
        """
        Deletes a Trunk.
        :param sid: A human readable 34 character unique identifier
        """
        return self.delete_instance(sid)
