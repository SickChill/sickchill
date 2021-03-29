"""
Test restart
"""

import unittest

from sickchill import settings
from sickchill.oldbeard.event_queue import Events
from sickchill.system.Restart import Restart


class RestartTests(unittest.TestCase):
    """
    Test restart
    """

    def test_restart(self):
        """
        Test restart
        """
        settings.PID = 123456
        settings.events = Events(None)

        test_cases = {
            0: False,
            "0": False,
            123: False,
            "123": False,
            123456: True,
            "123456": True,
        }

        unicode_test_cases = {
            "0": False,
            "123": False,
            "123456": True,
        }

        for tests in test_cases, unicode_test_cases:
            for (pid, result) in tests.items():
                assert Restart.restart(pid) == result


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(RestartTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
