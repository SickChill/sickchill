

"""
Tests for SickChill
"""

# Stdlib Imports
import unittest

# Local Folder Imports
from . import helper, providers, show, system

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests" <=====')

    TEST_MODULES = [
        helper,
        providers,
        show,
        system,
    ]

    for test_module in TEST_MODULES:
        SUITE = unittest.TestLoader().loadTestsFromModule(test_module)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
