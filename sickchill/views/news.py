import markdown2

import sickchill.start
from sickchill import logger, settings

from .common import PageTemplate
from .home import Home
from .routes import Route


@Route("/news(/?.*)", name="news")
class HomeNews(Home):
    def index(self):
        # noinspection PyBroadException
        try:
            news = settings.versionCheckScheduler.action.check_for_new_news()
        except Exception:
            logger.debug("Could not load news from repo, giving a link!")
            news = _("Could not load news from the repo. [Click here for news.md])({news_url})").format(news_url=settings.NEWS_URL)

        settings.NEWS_LAST_READ = settings.NEWS_LATEST
        settings.NEWS_UNREAD = 0
        sickchill.start.save_config()

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(news if news else _("The was a problem connecting to github, please refresh and try again"), extras=["header-ids"])

        return t.render(title=_("News"), header=_("News"), topmenu="system", data=data, controller="news", action="index")
