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
                            f"SickChill Notification - Snatched\nShow: {show[0]}\nEpisode Number: {show[1]}\nEpisode: {show[2]}\nQuality: {show[3]}\n\nPowered by SickChill."
                        )
                    )
                    msg.attach(
                        MIMEText(
                            f'<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Snatched</h3><p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p><p>Quality: <b>{show[3]}</b></p><h5 style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</h5></body>',
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
                    logger.debug(f'Snatch notification sent to [{to}] for "{ep_name}"')
                else:
                    logger.warning(f"Snatch notification error: {self.last_err}")

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
                            f"SickChill Notification - Downloaded\nShow: {show[0]}\nEpisode Number: {show[1]}\nEpisode: {show[2]}\nQuality: {show[3]}\n\nPowered by SickChill."
                        )
                    )
                    msg.attach(
                        MIMEText(
                            '<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Downloaded</h3><p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p><p>Quality: <b>{show[3]}</b></p><h5 style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</h5></body>',
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
                    logger.debug(f'Download notification sent to [{to}] for "{ep_name}"')
                else:
                    logger.warning(f"Download notification error: {self.last_err}")

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
                            f"SickChill Notification - Postprocessed\nShow: {show[0]}\nEpisode Number: {show[1]}\nEpisode: {show[2]}\nQuality: {show[3]}\n\nPowered by SickChill."
                        )
                    )
                    msg.attach(
                        MIMEText(
                            f'<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Postprocessed</h3><p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p><p>Quality: <b>{show[3]}</b></p><h5 style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</h5></body>',
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
                    logger.debug(f'Postprocess notification sent to [{to}] for "{ep_name}"')
                else:
                    logger.warning(f"Postprocess notification error: {self.last_err}")

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
                            f"SickChill Notification - Subtitle Downloaded\nShow: {show[0]}\nEpisode Number: {show[1]}\nEpisode: {show[2]}\nLanguage: {lang}\n\nPowered by SickChill."
                        )
                    )
                    msg.attach(
                        MIMEText(
                            f'<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Subtitle Downloaded</h3><p>Show: <b>{show[0]}</b></p><p>Episode Number: <b>{show[1]}</b></p><p>Episode: <b>{show[2]}</b></p></p><p>Language: <b>{lang}</b></p><h5 style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</h5></body>',
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
                    logger.debug(f'Download notification sent to [{to}] for "{ep_name}"')
                else:
                    logger.warning(f"Download notification error: {self.last_err}")

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
                    msg.attach(MIMEText(f"SickChill Notification - Updated\nCommit: {new_version}\n\nPowered by SickChill."))
                    msg.attach(
                        MIMEText(
                            f'<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Updated</h3><br><p>Commit: <b>{new_version}</b></p><br><br><footer style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</footer></body>',
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(new_version)
                    except Exception:
                        msg = MIMEText("SickChill updated")

                msg["Subject"] = f"Updated: {new_version}"
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug(f"Update notification sent to [{to}]")
                else:
                    logger.warning(f"Update notification error: {self.last_err}")

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
                    msg.attach(MIMEText(f"SickChill Notification - Remote Login\nNew login from IP: {ipaddress}\n\n" "Powered by SickChill."))
                    msg.attach(
                        MIMEText(
                            f'<body style="font-family:Helvetica, Arial, sans-serif;"><h3>SickChill Notification - Remote Login</h3><br><p>New login from IP: <a href="http://geomaplookup.net/?ip={ipaddress}">{ipaddress}</a>.<br><br><footer style="margin-top: 2.5em; padding: .7em 0; color: #777; border-top: #BBB solid 1px;">Powered by SickChill.</footer></body>',
                            "html",
                        )
                    )

                except Exception:
                    try:
                        msg = MIMEText(ipaddress)
                    except Exception:
                        msg = MIMEText("SickChill Remote Login")

                msg["Subject"] = f"New Login from IP: {ipaddress}"
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ",".join(to)
                msg["Date"] = formatdate(localtime=True)
                if self._sendmail(
                    settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_FROM, settings.EMAIL_TLS, settings.EMAIL_USER, settings.EMAIL_PASSWORD, to, msg
                ):
                    logger.debug(f"Login notification sent to [{to}]")
                else:
                    logger.warning(f"Login notification error: {self.last_err}")

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
        logger.debug(f"Notification recipients: {addrs}")
        return addrs

    def _sendmail(self, host, port, smtp_from, use_tls, user, pwd, to, msg, smtpDebug=False):
        logger.debug(f"HOST: {host}; PORT: {port}; FROM: {smtp_from}, TLS: {use_tls}, USER: {user}, PWD: {pwd}, TO: {to}")
        try:
            srv = smtplib.SMTP(host, int(port))
        except Exception as e:
            logger.warning("Exception generated while sending e-mail: " + str(e))
            # logger.debug(traceback.format_exc())
            self.last_err = f"{e}"
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
            self.last_err = f"{e}"
            return False

    @staticmethod
    def _parseEp(ep_name):
        sep = " - "
        titles = ep_name.split(sep)
        logger.debug(f"TITLES: {titles}")
        return titles
