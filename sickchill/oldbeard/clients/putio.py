from putiopy import Client as PutioClient, ClientError

from sickchill.oldbeard import helpers
from sickchill.oldbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super().__init__("put.io", host, username, password)
        self.url = "https://api.put.io/login"

    def _get_auth(self):
        client = PutioClient(self.password)
        try:
            client.Account.info()
        except ClientError as error:
            helpers.handle_requests_exception(error)
            self.auth = None
        else:
            self.auth = client

        return self.auth

    @property
    def _parent_id(self):
        parent_id = 0
        if self.username is not None and self.username != "":
            for f in self.auth.File.list():
                if f.name == self.username:
                    parent_id = f.id
                    break

        return parent_id

    def _add_torrent_uri(self, result):
        transfer = self.auth.Transfer.add_url(result.url, self._parent_id)

        return transfer.id is not None

    def _add_torrent_file(self, result):
        filename = result.name + ".torrent"
        transfer = self.auth.Transfer.add_torrent(filename, self._parent_id)

        return transfer.id is not None
