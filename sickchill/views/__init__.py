from sickchill.views.api import ApiCall, ApiHandler, function_mapper, KeyHandler
from sickchill.views.authentication import LoginHandler, LogoutHandler
from sickchill.views.browser import WebFileBrowser
from sickchill.views.calendar import CalendarHandler
from sickchill.views.changelog import HomeChangeLog
from sickchill.views.common import PageTemplate
from sickchill.views.config import (
    Config,
    ConfigAnime,
    ConfigBackupRestore,
    ConfigNotifications,
    ConfigPostProcessing,
    ConfigProviders,
    ConfigSearch,
    ConfigShares,
    ConfigSubtitles,
)
from sickchill.views.history import History
from sickchill.views.home import Home
from sickchill.views.imageSelector import ImageSelector
from sickchill.views.index import BaseHandler, WebHandler, WebRoot
from sickchill.views.logs import ErrorLogs
from sickchill.views.manage import AddShows, Manage, ManageSearches, PostProcess
from sickchill.views.movies import MoviesHandler
from sickchill.views.news import HomeNews
from sickchill.views.routes import Route
