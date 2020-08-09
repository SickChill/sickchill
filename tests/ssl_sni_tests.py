
"""
Test SNI and SSL
"""

import unittest

import certifi
import requests

from sickchill.oldbeard import providers as providers


def generator(_provider):
    """
    Generate tests for each provider

    :param _provider: to generate tests from
    :return: test
    """
    def _connectivity_test():
        """
        Generate tests
        :return: test to run
        """
        if not _provider.url:
            print('{0} has no url set, skipping'.format(_provider.name))
            return

        try:
            requests.head(_provider.url, verify=certifi.where(), timeout=10)
        except requests.exceptions.SSLError as error:
            if 'certificate verify failed' in str(error):
                print('Cannot verify certificate for {0}'.format(_provider.name))
            else:
                print('SSLError on {0}: {1}'.format(_provider.name, str(error)))
                raise
        except requests.exceptions.Timeout:
            print('Provider timed out')

    return _connectivity_test


class SniTests(unittest.TestCase):
    pass

if __name__ == "__main__":
    print("==================")
    print("STARTING - Provider Connectivity TESTS and SSL/SNI")
    print("==================")
    print("######################################################################")
    # Just checking all providers - we should make this error on non-existent urls.
    for provider in [p for p in providers.makeProviderList()]:
        test_name = 'test_{0}'.format(provider.name)
        test = generator(provider)
        setattr(SniTests, test_name, test)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(SniTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
