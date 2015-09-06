from datetime import datetime
from datetime import timedelta
from sickbeard.db import DBConnection


class History:
    date_format = '%Y%m%d%H%M%S'

    def __init__(self):
        self.db = DBConnection()

    def clear(self):
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE 1=1'
        )

    def trim(self):
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE date < ?',
            [(datetime.today() - timedelta(days=30)).strftime(History.date_format)]
        )
