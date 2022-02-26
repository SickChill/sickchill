"""
Test history
"""

import unittest


class HistoryTests(unittest.TestCase):
    """
    Test history
    """


if __name__ == "__main__":
    print("=====> Testing {0}".format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
