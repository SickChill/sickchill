# coding=utf-8

# Authors:
# Derek Battams <derek@battams.ca>
# Pedro Jose Pereira Vieito (@pvieito) <pvieito@gmail.com>
#
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
#
##############################################################################

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import ast
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

# First Party Imports
import sickbeard
from sickbeard import db, logger, filters
from sickchill.helper.encoding import ss


class Notifier(object):
    def __init__(self):
        self.last_err = None

    def test_notify(self, host, port, smtp_from, use_tls, user, pwd, to):
        msg = MIMEText('This is a test message from SickChill.  If you\'re reading this, the test succeeded.')
        if sickbeard.EMAIL_SUBJECT:
            msg[b'Subject'] = '[TEST] ' + sickbeard.EMAIL_SUBJECT
        else:
            msg[b'Subject'] = 'SickChill: Test Message'

        msg[b'From'] = smtp_from
        msg[b'To'] = to
        msg[b'Date'] = formatdate(localtime=True)
        return self._sendmail(host, port, smtp_from, use_tls, user, pwd, [to], msg, True)

    def notify_snatch(self, ep_name, title='Snatched:'):
        '''
        Send a notification that an episode was snatched

        ep_name: The name of the episode that was snatched
        title: The title of the notification (optional)
        '''
        ep_name = ss(ep_name)

        if sickbeard.USE_EMAIL and sickbeard.EMAIL_NOTIFY_ONSNATCH:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Snatched\n'
                        'Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n'
                        'Powered by SickChill.'.format(show[0], show[1], show[2], show[3])))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Snatched</h3>'
                        '<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>'
                        '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</h5></body>'.format(show[0], show[1], show[2], show[3]),
                        'html'))

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText('Episode Snatched')

                if sickbeard.EMAIL_SUBJECT:
                    msg[b'Subject'] = '[SN] ' + sickbeard.EMAIL_SUBJECT
                else:
                    msg[b'Subject'] = 'Snatched: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Snatch notification sent to [{0}] for "{1}"'.format(to, ep_name), logger.DEBUG)
                else:
                    logger.log('Snatch notification error: {0}'.format(self.last_err), logger.WARNING)

    def notify_download(self, ep_name, title='Completed:'):
        '''
        Send a notification that an episode was downloaded

        ep_name: The name of the episode that was downloaded
        title: The title of the notification (optional)
        '''
        ep_name = ss(ep_name)

        if sickbeard.USE_EMAIL and sickbeard.EMAIL_NOTIFY_ONDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Downloaded\n'
                        'Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n'
                        'Powered by SickChill.'.format(show[0], show[1], show[2], show[3])))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Downloaded</h3>'
                        '<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>'
                        '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</h5></body>'.format(show[0], show[1], show[2], show[3]),
                        'html'))

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText('Episode Downloaded')

                if sickbeard.EMAIL_SUBJECT:
                    msg[b'Subject'] = '[DL] ' + sickbeard.EMAIL_SUBJECT
                else:
                    msg[b'Subject'] = 'Downloaded: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Download notification sent to [{0}] for "{1}"'.format(to, ep_name), logger.DEBUG)
                else:
                    logger.log('Download notification error: {0}'.format(self.last_err), logger.WARNING)

    def notify_postprocess(self, ep_name, title='Postprocessed:'):
        '''
        Send a notification that an episode was postprocessed

        ep_name: The name of the episode that was postprocessed
        title: The title of the notification (optional)
        '''
        ep_name = ss(ep_name)

        if sickbeard.USE_EMAIL and sickbeard.EMAIL_NOTIFY_ONPOSTPROCESS:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Postprocessed\n'
                        'Show: {0}\nEpisode Number: {1}\nEpisode: {2}\nQuality: {3}\n\n'
                        'Powered by SickChill.'.format(show[0], show[1], show[2], show[3])))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Postprocessed</h3>'
                        '<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p><p>Quality: <b>{3}</b></p>'
                        '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</h5></body>'.format(show[0], show[1], show[2], show[3]),
                        'html'))

                except Exception:
                    try:
                        msg = MIMEText(ep_name)
                    except Exception:
                        msg = MIMEText('Episode Postprocessed')

                if sickbeard.EMAIL_SUBJECT:
                    msg[b'Subject'] = '[PP] ' + sickbeard.EMAIL_SUBJECT
                else:
                    msg[b'Subject'] = 'Postprocessed: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Postprocess notification sent to [{0}] for "{1}"'.format(to, ep_name), logger.DEBUG)
                else:
                    logger.log('Postprocess notification error: {0}'.format(self.last_err), logger.WARNING)

    def notify_subtitle_download(self, ep_name, lang, title='Downloaded subtitle:'):
        '''
        Send a notification that an subtitle was downloaded

        ep_name: The name of the episode that was downloaded
        lang: Subtitle language wanted
        '''
        ep_name = ss(ep_name)

        if sickbeard.USE_EMAIL and sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parseEp(ep_name)
            to = self._generate_recipients(show)
            if not to:
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Subtitle Downloaded\n'
                        'Show: {0}\nEpisode Number: {1}\nEpisode: {2}\n'
                        'Language: {3}\n\n'
                        'Powered by SickChill.'.format(show[0], show[1], show[2], lang)))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Subtitle Downloaded</h3>'
                        '<p>Show: <b>{0}</b></p><p>Episode Number: <b>{1}</b></p><p>Episode: <b>{2}</b></p></p>'
                        '<p>Language: <b>{3}</b></p>'
                        '<h5 style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</h5></body>'.format(show[0], show[1], show[2], lang),
                        'html'))
                except Exception:
                    try:
                        msg = MIMEText(ep_name + ': ' + lang)
                    except Exception:
                        msg = MIMEText('Episode Subtitle Downloaded')

                if sickbeard.EMAIL_SUBJECT:
                    msg[b'Subject'] = '[ST] ' + sickbeard.EMAIL_SUBJECT
                else:
                    msg[b'Subject'] = lang + ' Subtitle Downloaded: ' + ep_name
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Download notification sent to [{0}] for "{1}"'.format(to, ep_name), logger.DEBUG)
                else:
                    logger.log('Download notification error: {0}'.format(self.last_err), logger.WARNING)

    def notify_git_update(self, new_version='??'):
        '''
        Send a notification that SickChill was updated
        new_version: The commit SickChill was updated to
        '''
        if sickbeard.USE_EMAIL:
            to = self._generate_recipients(None)
            if not to:
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Updated\n'
                        'Commit: {}\n\n'
                        'Powered by SickChill.'.format(new_version)))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Updated</h3><br>'
                        '<p>Commit: <b>{}</b></p><br><br>'
                        '<footer style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</footer></body>'.format
                        (new_version), 'html'))

                except Exception:
                    try:
                        msg = MIMEText(new_version)
                    except Exception:
                        msg = MIMEText('SickChill updated')

                msg[b'Subject'] = 'Updated: {0}'.format(new_version)
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Update notification sent to [{0}]'.format(to), logger.DEBUG)
                else:
                    logger.log('Update notification error: {0}'.format(self.last_err), logger.WARNING)

    def notify_login(self, ipaddress=''):
        '''
        Send a notification that SickChill was logged into remotely
        ipaddress: The ip SickChill was logged into from
        '''
        if sickbeard.USE_EMAIL:
            to = self._generate_recipients(None)
            if not len(to):
                logger.log('Skipping email notify because there are no configured recipients', logger.DEBUG)
            else:
                try:
                    msg = MIMEMultipart('alternative')
                    msg.attach(MIMEText(
                        'SickChill Notification - Remote Login\n'
                        'New login from IP: {0}\n\n'
                        'Powered by SickChill.'.format(ipaddress)))
                    msg.attach(MIMEText(
                        '<body style="font-family:Helvetica, Arial, sans-serif;">'
                        '<h3>SickChill Notification - Remote Login</h3><br>'
                        '<p>New login from IP: <a href="http://geomaplookup.net/?ip={0}">{0}</a>.<br><br>'
                        '<footer style="margin-top: 2.5em; padding: .7em 0; '
                        'color: #777; border-top: #BBB solid 1px;">'
                        'Powered by SickChill.</footer></body>'.format
                        (ipaddress), 'html'))

                except Exception:
                    try:
                        msg = MIMEText(ipaddress)
                    except Exception:
                        msg = MIMEText('SickChill Remote Login')

                msg[b'Subject'] = 'New Login from IP: {0}'.format(ipaddress)
                msg[b'From'] = sickbeard.EMAIL_FROM
                msg[b'To'] = ','.join(to)
                msg[b'Date'] = formatdate(localtime=True)
                if self._sendmail(sickbeard.EMAIL_HOST, sickbeard.EMAIL_PORT, sickbeard.EMAIL_FROM, sickbeard.EMAIL_TLS,
                                  sickbeard.EMAIL_USER, sickbeard.EMAIL_PASSWORD, to, msg):
                    logger.log('Login notification sent to [{0}]'.format(to), logger.DEBUG)
                else:
                    logger.log('Login notification error: {0}'.format(self.last_err), logger.WARNING)

    @staticmethod
    def _generate_recipients(show):
        addrs = []
        main_db_con = db.DBConnection()

        # Grab the global recipients
        if sickbeard.EMAIL_LIST:
            for addr in sickbeard.EMAIL_LIST.split(','):
                if len(addr.strip()) > 0:
                    addrs.append(addr)

        # Grab the per-show-notification recipients
        if show is not None:
            for s in show:
                for subs in main_db_con.select('SELECT notify_list FROM tv_shows WHERE show_name = ?', (s,)):
                    if subs[b'notify_list']:
                        if subs[b'notify_list'][0] == '{':
                            entries = dict(ast.literal_eval(subs[b'notify_list']))
                            for addr in entries[b'emails'].split(','):
                                if len(addr.strip()) > 0:
                                    addrs.append(addr)
                        else:                                           # Legacy
                            for addr in subs[b'notify_list'].split(','):
                                if len(addr.strip()) > 0:
                                    addrs.append(addr)

        addrs = set(addrs)
        logger.log('Notification recipients: {0}'.format(addrs), logger.DEBUG)
        return addrs

    def _sendmail(self, host, port, smtp_from, use_tls, user, pwd, to, msg, smtpDebug=False):
        logger.log('HOST: {0}; PORT: {1}; FROM: {2}, TLS: {3}, USER: {4}, PWD: {5}, TO: {6}'.format(
            host, port, smtp_from, use_tls, user, pwd, to), logger.DEBUG)
        try:
            srv = smtplib.SMTP(host, int(port))
        except Exception as e:
            logger.log('Exception generated while sending e-mail: ' + str(e), logger.WARNING)
            # logger.log(traceback.format_exc(), logger.DEBUG)
            self.last_err = '{0}'.format(e)
            return False

        if smtpDebug:
            srv.set_debuglevel(1)
        try:
            if use_tls in ('1', True) or (user and pwd):
                logger.log('Sending initial EHLO command!', logger.DEBUG)
                srv.ehlo()
            if use_tls in ('1', True):
                logger.log('Sending STARTTLS command!', logger.DEBUG)
                srv.starttls()
                srv.ehlo()
            if user and pwd:
                logger.log('Sending LOGIN command!', logger.DEBUG)
                srv.login(user.encode('utf-8'), pwd.encode('utf-8'))

            srv.sendmail(smtp_from, to, msg.as_string())
            srv.quit()
            return True
        except Exception as e:
            self.last_err = '{0}'.format(e)
            return False

    @staticmethod
    def _parseEp(ep_name):
        ep_name = ss(ep_name)

        sep = ' - '
        titles = ep_name.split(sep)
        logger.log('TITLES: {0}'.format(titles), logger.DEBUG)
        return titles
