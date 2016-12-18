from . import InstanceResource, ListResource


class Transcription(InstanceResource):

    def delete(self):
        """
        Delete this transcription
        """
        return self.parent.delete(self.name)


class Transcriptions(ListResource):

    name = "Transcriptions"
    instance = Transcription

    def list(self, **kwargs):
        """
        Return a list of :class:`Transcription` resources
        """
        return self.get_instances(kwargs)

    def delete(self, sid):
        """
        Delete the given transcription
        """
        return self.delete_instance(sid)
