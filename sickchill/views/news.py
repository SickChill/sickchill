# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# Third Party Imports
import markdown2

# First Party Imports
import sickbeard
import sickchill.start
from sickbeard import logger
from sickchill import settings

# Local Folder Imports
from .common import PageTemplate
from .home import Home
from .routes import Route


@Route('/news(/?.*)', name='news')
class HomeNews(Home):
    def __init__(self, *args, **kwargs):
        super(HomeNews, self).__init__(*args, **kwargs)

    def index(self):
        # noinspection PyBroadException
        try:
            news = settings.versionCheckScheduler.action.check_for_new_news()
        except Exception:
            logger.debug('Could not load news from repo, giving a link!')
            news = _('Could not load news from the repo. [Click here for news.md])({news_url})').format(news_url=settings.NEWS_URL)

        settings.NEWS_LAST_READ = settings.NEWS_LATEST
        settings.NEWS_UNREAD = 0
        sickchill.start.save_config()

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(news if news else _("The was a problem connecting to github, please refresh and try again"), extras=['header-ids'])

        return t.render(title=_("News"), header=_("News"), topmenu="system", data=data, controller="news", action="index")
