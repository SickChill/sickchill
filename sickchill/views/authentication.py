from sickchill import logger, settings

from ..oldbeard import config, notifiers
from .common import PageTemplate
from .index import BaseHandler

login_error = ""


class LoginHandler(BaseHandler):
    def get(self, next_=None):
        next_ = self.get_query_argument("next", next_)
        if self.get_current_user():
            self.redirect(next_ or "/" + settings.DEFAULT_PAGE + "/")
        else:
            t = PageTemplate(rh=self, filename="login.mako")
            self.finish(t.render(title=_("Login"), header=_("Login"), topmenu="login", login_error=login_error))

    def post(self, next_=None):
        notifiers.notify_login(self.request.remote_ip)
        global login_error

        if self.get_body_argument("username", None) == settings.WEB_USERNAME and self.get_body_argument("password", None) == settings.WEB_PASSWORD:
            login_error = ""
            remember_me = config.checkbox_to_value(self.get_body_argument("remember_me", "0"))
            self.set_secure_cookie("sickchill_user", settings.API_KEY, expires_days=(None, 30)[remember_me])
            logger.info(_("User logged into the SickChill web interface"))
        else:
            logger.warning(_("User attempted a failed login to the SickChill web interface from IP: ") + self.request.remote_ip)
            login_error = _("Incorrect username or password! Both username and password are case sensitive!")

        next_ = self.get_query_argument("next", next_)
        self.redirect(next_ or "/" + settings.DEFAULT_PAGE + "/")


class LogoutHandler(BaseHandler):
    def get(self, next_=None):
        self.clear_cookie("sickchill_user")
        self.redirect("/login/")
