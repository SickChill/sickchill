"""
Test exception logging
"""

import unittest

from sickchill import logger


def exception_generator():
    """
    Dummy function to raise a fake exception and log it
    """
    try:
        raise Exception('FAKE EXCEPTION')
    except Exception as error:
        logger.exception("FAKE ERROR: " + str(error))
        logger.submit_errors()
        raise


class IssueSubmitterBasicTests(unittest.TestCase):
    """
    Tests logging of exceptions
    """
    def test_submitter(self):
        """
        Test that an exception is raised
        """
        self.assertRaises(Exception, exception_generator)


if __name__ == "__main__":
    print("==================")
    print("STARTING - ISSUE SUBMITTER TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(IssueSubmitterBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
