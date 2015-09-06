from datetime import datetime
from datetime import timedelta
from sickbeard.common import Quality
from sickbeard.db import DBConnection


class History:
    date_format = '%Y%m%d%H%M%S'

    def __init__(self):
        self.db = DBConnection()

    def clear(self):
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE 1 = 1'
        )

    def get(self, limit=100, action=None):
        action = action.lower() if isinstance(action, str) else ''
        limit = int(limit)

        if action == 'downloaded':
            actions = Quality.DOWNLOADED
        elif action == 'snatched':
            actions = Quality.SNATCHED
        else:
            actions = Quality.SNATCHED + Quality.DOWNLOADED

        if limit == 0:
            results = self.db.select(
                'SELECT h.*, show_name '
                'FROM history h, tv_shows s '
                'WHERE h.showid = s.indexer_id '
                'AND action in (' + ','.join(['?'] * len(actions)) + ') '
                                                                     'ORDER BY date DESC',
                actions
            )
        else:
            results = self.db.select(
                'SELECT h.*, show_name '
                'FROM history h, tv_shows s '
                'WHERE h.showid = s.indexer_id '
                'AND action in (' + ','.join(['?'] * len(actions)) + ') '
                                                                     'ORDER BY date DESC '
                                                                     'LIMIT ?',
                actions + [limit]
            )

        data = []
        for result in results:
            data.append({
                'action': result['action'],
                'date': result['date'],
                'episode': result['episode'],
                'provider': result['provider'],
                'quality': result['quality'],
                'resource': result['resource'],
                'season': result['season'],
                'show_id': result['showid'],
                'show_name': result['show_name']
            })

        return data

    def trim(self):
        self.db.action(
            'DELETE '
            'FROM history '
            'WHERE date < ?',
            [(datetime.today() - timedelta(days=30)).strftime(History.date_format)]
        )
