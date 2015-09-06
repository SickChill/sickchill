from sickbeard.db import DBConnection


class History:
    def __init__(self):
        self.db = DBConnection()

    def clear(self):
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE 1=1'
        )
