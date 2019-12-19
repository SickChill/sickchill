# coding=UTF-8
# URL: https://github.com/SickChill/SickChill
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

###
# As a test case, there are instances in which it is necessary to call protected members of
# classes in order to test those classes.  Therefore we will be pylint disable protected-access
###

# pylint: disable=line-too-long

"""
Test notifiers
"""


import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import db
from sickbeard.tv import TVEpisode, TVShow
from sickchill.views.home import Home
from sickbeard.notifiers.emailnotify import Notifier as EmailNotifier
from sickbeard.notifiers.prowl import Notifier as ProwlNotifier
from sickchill.helper.encoding import ss
import tests.test_lib as test


class NotifierTests(test.SickbeardTestDBCase):  # pylint: disable=too-many-public-methods
    """
    Test notifiers
    """
    @classmethod
    def setUpClass(cls):
        num_legacy_shows = 3
        num_shows = 3
        num_episodes_per_show = 5
        cls.mydb = db.DBConnection()
        cls.legacy_shows = []
        cls.shows = []

        # Per-show-notifications were originally added for email notifications only.  To add
        # this feature to other notifiers, it was necessary to alter the way text is stored in
        # one of the DB columns.  Therefore, to test properly, we must create some shows that
        # store emails in the old method (legacy method) and then other shows that will use
        # the new method.
        for show_counter in range(100, 100 + num_legacy_shows):
            show = TVShow(1, show_counter)
            show.name = "Show " + str(show_counter)
            show.episodes = []
            for episode_counter in range(0, num_episodes_per_show):
                episode = TVEpisode(show, test.SEASON, episode_counter)
                episode.name = "Episode " + str(episode_counter + 1)
                episode.quality = "SDTV"
                show.episodes.append(episode)
            show.saveToDB()
            cls.legacy_shows.append(show)

        for show_counter in range(200, 200 + num_shows):
            show = TVShow(1, show_counter)
            show.name = "Show " + str(show_counter)
            show.episodes = []
            for episode_counter in range(0, num_episodes_per_show):
                episode = TVEpisode(show, test.SEASON, episode_counter)
                episode.name = "Episode " + str(episode_counter + 1)
                episode.quality = "SDTV"
                show.episodes.append(episode)
            show.saveToDB()
            cls.shows.append(show)

    def setUp(self):
        """
        Set up tests
        """
        self._debug_spew("\n\r")

    @unittest.skip('Not yet implemented')
    def test_boxcar(self):
        """
        Test boxcar notifications
        """
        pass

    def test_email(self):
        """
        Test email notifications
        """
        email_notifier = EmailNotifier()

        # Per-show-email notifications were added early on and utilized a different format than the other notifiers.
        # Therefore, to test properly (and ensure backwards compatibility), this routine will test shows that use
        # both the old and the new storage methodology
        legacy_test_emails = "email-1@address.com,email2@address.org,email_3@address.tv"
        test_emails = "email-4@address.com,email5@address.org,email_6@address.tv"

        for show in self.legacy_shows:
            showid = self._get_showid_by_showname(show.name)
            self.mydb.action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [legacy_test_emails, showid])

        for show in self.shows:
            showid = self._get_showid_by_showname(show.name)
            Home.saveShowNotifyList(show=showid, emails=test_emails)

        # Now, iterate through all shows using the email list generation routines that are used in the notifier proper
        shows = self.legacy_shows + self.shows
        for show in shows:
            for episode in show.episodes:
                ep_name = ss(episode._format_pattern('%SN - %Sx%0E - %EN - ') + episode.quality)  # pylint: disable=protected-access
                show_name = email_notifier._parseEp(ep_name)  # pylint: disable=protected-access
                recipients = email_notifier._generate_recipients(show_name)  # pylint: disable=protected-access
                self._debug_spew("- Email Notifications for " + show.name + " (episode: " + episode.name + ") will be sent to:")
                for email in recipients:
                    self._debug_spew("-- " + email.strip())
                self._debug_spew("\n\r")

        return True

    @unittest.skip('Not yet implemented')
    def test_emby(self):
        """
        Test emby notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_freemobile(self):
        """
        Test freemobile notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_growl(self):
        """
        Test growl notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_kodi(self):
        """
        Test kodi notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_libnotify(self):
        """
        Test libnotify notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_nma(self):
        """
        Test nma notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_nmj(self):
        """
        Test nmj notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_nmjv2(self):
        """
        Test nmjv2 notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_plex(self):
        """
        Test plex notifications
        """
        pass

    def test_prowl(self):
        """
        Test prowl notifications
        """
        prowl_notifier = ProwlNotifier()

        # Prowl per-show-notifications only utilize the new methodology for storage; therefore, the list of legacy_shows
        # will not be altered (to preserve backwards compatibility testing)
        test_prowl_apis = "11111111111111111111,22222222222222222222"

        for show in self.shows:
            showid = self._get_showid_by_showname(show.name)
            Home.saveShowNotifyList(show=showid, prowlAPIs=test_prowl_apis)

        # Now, iterate through all shows using the Prowl API generation routines that are used in the notifier proper
        for show in self.shows:
            for episode in show.episodes:
                ep_name = ss(episode._format_pattern('%SN - %Sx%0E - %EN - ') + episode.quality)  # pylint: disable=protected-access
                show_name = prowl_notifier._parse_episode(ep_name)  # pylint: disable=protected-access
                recipients = prowl_notifier._generate_recipients(show_name)  # pylint: disable=protected-access
                self._debug_spew("- Prowl Notifications for " + show.name + " (episode: " + episode.name + ") will be sent to:")
                for api in recipients:
                    self._debug_spew("-- " + api.strip())
                self._debug_spew("\n\r")

        return True

    @unittest.skip('Not yet implemented')
    def test_pushalot(self):
        """
        Test pushalot notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_pushbullet(self):
        """
        Test pushbullet notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_pushover(self):
        """
        Test pushover notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_pytivo(self):
        """
        Test pytivo notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_synoindex(self):
        """
        Test synoindex notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_synologynotifier(self):
        """
        Test synologynotifier notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_trakt(self):
        """
        Test trakt notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_tweet(self):
        """
        Test tweet notifications
        """
        pass

    @unittest.skip('Not yet implemented')
    def test_twilio(self):
        """
        Test twilio notifications
        """
        pass

    @staticmethod
    def _debug_spew(text):
        """
        Spew text notifications

        :param text: to spew
        :return:
        """
        if __name__ == '__main__' and text is not None:
            print(text)

    def _get_showid_by_showname(self, showname):
        """
        Get show ID by show name

        :param showname:
        :return:
        """
        if showname is not None:
            rows = self.mydb.select("SELECT show_id FROM tv_shows WHERE show_name = ?", [showname])
            if len(rows) == 1:
                return rows[0][b'show_id']
        return -1

if __name__ == '__main__':
    print("==================")
    print("STARTING - NOTIFIER TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(NotifierTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
