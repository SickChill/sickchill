import ast
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from sickchill import logger, settings
from sickchill.oldbeard import db


class Notifier(object):
    def __init__(self):
        self.last_err = None

    def test_notify(self, host, port, smtp_from, use_tls, user, pwd, to):
        msg = MIMEText("This is a test message from SickChill.  If you're reading this, the test succeeded.")
        if settings.EMAIL_SUBJECT:
            msg["Subject"] = "[TEST] " + settings.EMAIL_SUBJECT
        else:
            msg["Subject"] = "SickChill: Test Message"

        msg["From"] = smtp_from
        msg["To"] = to
        msg["Date"] = formatdate(localtime=True)
        return self._sendmail(host, port, smtp_from, use_tls, user, pwd, [to], msg, True)

    def notify_snatch(self, ep_name, title="Snatched:"):
        """
        Send a notification that an episode was snatched

        ep_name: The name of the episode that was snatched
        title: The title of the notification (optional)
        """
        if settings.USE_EMAIL and settings.EMAIL_NOTIFY_ONSNATCH:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(
                        MIMEText(
                            "SickChill Notification - Snatched\n"
                            "Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n"
                            "Powered by SickChill.".format(show[0], show[1], show[2], show[3])
                        )
                    )
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Snatched</h3>"
                            "<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>"
                            '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</h5></body>".format(show[0], show[1], show[2], show[3]),
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText("Episode Snatched")

                if settings.EMAIL_SUBJECT:
                    msg["Subject"] = "[SN] " + settings.EMAIL_SUBJECT
                else:
                    msg["Subject"] = "Snatched: " + ep_name
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug('Snatch notification sent to [{0}] for "{1}"'.format(to, ep_name))
                else:
                    logger.warning("Snatch notification error: {0}".format(self.last_err))

    def notify_download(self, ep_name, title="Completed:"):
        """
        Send a notification that an episode was downloaded

        ep_name: The name of the episode that was downloaded
        title: The title of the notification (optional)
        """
        if settings.USE_EMAIL and settings.EMAIL_NOTIFY_ONDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(
                        MIMEText(
                            "SickChill Notification - Downloaded\n"
                            "Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n"
                            "Powered by SickChill.".format(show[0], show[1], show[2], show[3])
                        )
                    )
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Downloaded</h3>"
                            "<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>"
                            '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</h5></body>".format(show[0], show[1], show[2], show[3]),
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText("Episode Downloaded")

                if settings.EMAIL_SUBJECT:
                    msg["Subject"] = "[DL] " + settings.EMAIL_SUBJECT
                else:
                    msg["Subject"] = "Downloaded: " + ep_name
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug('Download notification sent to [{0}] for "{1}"'.format(to, ep_name))
                else:
                    logger.warning("Download notification error: {0}".format(self.last_err))

    def notify_postprocess(self, ep_name, title="Postprocessed:"):
        """
        Send a notification that an episode was postprocessed

        ep_name: The name of the episode that was postprocessed
        title: The title of the notification (optional)
        """
        if settings.USE_EMAIL and settings.EMAIL_NOTIFY_ONPOSTPROCESS:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(
                        MIMEText(
                            "SickChill Notification - Postprocessed\n"
                            "Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n"
                            "Powered by SickChill.".format(show[0], show[1], show[2], show[3])
                        )
                    )
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Postprocessed</h3>"
                            "<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>"
                            '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</h5></body>".format(show[0], show[1], show[2], show[3]),
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText("Episode Postprocessed")

                if settings.EMAIL_SUBJECT:
                    msg["Subject"] = "[PP] " + settings.EMAIL_SUBJECT
                else:
                    msg["Subject"] = "Postprocessed: " + ep_name
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug('Postprocess notification sent to [{0}] for "{1}"'.format(to, ep_name))
                else:
                    logger.warning("Postprocess notification error: {0}".format(self.last_err))

    def notify_subtitle_download(self, ep_name, lang, title="Downloaded subtitle:"):
        """
        Send a notification that an subtitle was downloaded

        ep_name: The name of the episode that was downloaded
        lang: Subtitle language wanted
        """
        if settings.USE_EMAIL and settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(
                        MIMEText(
                            "SickChill Notification - Subtitle Downloaded\n"
                            "Show: {0}\nEpisode Number: {1}\nEpisode: {2}\n"
                            "Language: {3}\n\n"
                            "Powered by SickChill.".format(show[0], show[1], show[2], lang)
                        )
                    )
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Subtitle Downloaded</h3>"
                            "<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p></p>"
                            "<p>Language: <b>{3}</b></p>"
                            '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</h5></body>".format(show[0], show[1], show[2], lang),
                            "html",
                        )
                    )
                except Exception:
                    try:
                        msg = MIMEText(ep_name + ": " + lang)
                    except Exception:
                        msg = MIMEText("Episode Subtitle Downloaded")

                if settings.EMAIL_SUBJECT:
                    msg["Subject"] = "[ST] " + settings.EMAIL_SUBJECT
                else:
                    msg["Subject"] = lang + " Subtitle Downloaded: " + ep_name
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug('Download notification sent to [{0}] for "{1}"'.format(to, ep_name))
                else:
                    logger.warning("Download notification error: {0}".format(self.last_err))

    def notify_git_update(self, new_version="??"):
        """
        Send a notification that SickChill was updated
        new_version: The commit SickChill was updated to
        """
        if settings.USE_EMAIL:
            to = self._generate_recipients(None)
            if not to:
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(MIMEText("SickChill Notification - Updated\n" "Commit: {}\n\n" "Powered by SickChill.".format(new_version)))
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Updated</h3><br>"
                            "<p>Commit: <b>{}</b></p><br><br>"
                            '<footer style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</footer></body>".format(new_version),
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(new_version)
                    except Exception:
                        msg = MIMEText("SickChill updated")

                msg["Subject"] = "Updated: {0}".format(new_version)
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug("Update notification sent to [{0}]".format(to))
                else:
                    logger.warning("Update notification error: {0}".format(self.last_err))

    def notify_login(self, ipaddress=""):
        """
        Send a notification that SickChill was logged into remotely
        ipaddress: The ip SickChill was logged into from
        """
        if settings.USE_EMAIL:
            to = self._generate_recipients(None)
            if not len(to):
                logger.debug("Skipping email notify because there are no configured recipients")
            else:
                try:
                    msg = MIMEMultipart("alternative")
                    msg.attach(MIMEText("SickChill Notification - Remote Login\n" "New login from IP: {0}\n\n" "Powered by SickChill.".format(ipaddress)))
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;">'
                            "<h3>SickChill Notification - Remote Login</h3><br>"
                            '<p>New login from IP: <a href="http://geomaplookup.net/?ip={0}">{0}</a>.<br><br>'
                            '<footer style="margin-top: 2.5em; padding: .7em 0; '
                            'color: #777; border-top: #BBB solid 1px;">'
                            "Powered by SickChill.</footer></body>".format(ipaddress),
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(ipaddress)
                    except Exception:
                        msg = MIMEText("SickChill Remote Login")

                msg["Subject"] = "New Login from IP: {0}".format(ipaddress)
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug("Login notification sent to [{0}]".format(to))
                else:
                    logger.warning("Login notification error: {0}".format(self.last_err))

    @staticmethod
    def _generate_recipients(show):
        addrs = []
        main_db_con = db.DBConnection()

        # Grab the global recipients
        if settings.EMAIL_LIST:
            for addr in settings.EMAIL_LIST.split(","):
                if addr.strip():
                    addrs.append(addr)

        # Grab the per-show-notification recipients
        if show is not None:
            for s in show:
                for subs in main_db_con.select("SELECT notify_list FROM tv_shows WHERE show_name = ?", (s,)):
                    if subs["notify_list"]:
                        if subs["notify_list"][0] == "{":
                            entries = dict(ast.literal_eval(subs["notify_list"]))
                            for addr in entries["emails"].split(","):
                                if addr.strip():
                                    addrs.append(addr)
                        else:  # Legacy
                            for addr in subs["notify_list"].split(","):
                                if addr.strip():
                                    addrs.append(addr)

        addrs = set(addrs)
        logger.debug("Notification recipients: {0}".format(addrs))
        return addrs

    def _sendmail(self, host, port, smtp_from, use_tls, user, pwd, to, msg, smtpDebug=False):
        logger.debug("HOST: {0}; PORT: {1}; FROM: {2}, TLS: {3}, USER: {4}, PWD: {5}, TO: {6}".format(host, port, smtp_from, use_tls, user, pwd, to))
        try:
            srv = smtplib.SMTP(host, int(port))
        except Exception as e:
            logger.warning("Exception generated while sending e-mail: " + str(e))
            # logger.debug(traceback.format_exc())
            self.last_err = "{0}".format(e)
            return False

        if smtpDebug:
            srv.set_debuglevel(1)
        try:
            if use_tls in ("1", True) or (user and pwd):
                logger.debug("Sending initial EHLO command!")
                srv.ehlo()
            if use_tls in ("1", True):
                logger.debug("Sending STARTTLS command!")
                srv.starttls()
                srv.ehlo()
            if user and pwd:
                logger.debug("Sending LOGIN command!")
                srv.login(user, pwd)

            srv.sendmail(smtp_from, to, msg.as_string())
            srv.quit()
            return True
        except Exception as e:
            self.last_err = "{0}".format(e)
            return False

    @staticmethod
    def _parseEp(ep_name):
        sep = " - "
        titles = ep_name.split(sep)
        logger.debug("TITLES: {0}".format(titles))
        return titles
