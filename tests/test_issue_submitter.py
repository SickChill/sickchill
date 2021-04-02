"""
Test exception logging
"""

import unittest
import pytest

from sickchill import logger


class IssueSubmitterBasicTests(unittest.TestCase):
    """
    Tests logging of exceptions
    """

    def test_submitter(self):
        """
        Test that an exception is raised
        """
        try:
            with pytest.raises(Exception):
                raise Exception("FAKE EXCEPTION")
        except Exception as error:
            logger.exception("FAKE ERROR: " + str(error))
            logger.submit_errors()
            with pytest.raises(Exception):
                raise


if __name__ == "__main__":
    print("==================")
    print("STARTING - ISSUE SUBMITTER TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(IssueSubmitterBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
