import logging
import logging.config
import sys

from _pytest.unittest import UnitTestCase

logging.config.fileConfig("log_tests.ini")


def is_unittest(obj):
    """Is obj a subclass of unittest.TestCase?

    Lifted from older versions of py.test, as this seems to be removed.

    """
    unittest = sys.modules.get("unittest")
    if unittest is None:
        return  # nobody can have derived unittest.TestCase
    try:
        return issubclass(obj, unittest.TestCase)
    except KeyboardInterrupt:
        raise
    except Exception:
        return False


def pytest_pycollect_makeitem(collector, name, obj):
    if is_unittest(obj) and not obj.__name__.startswith("_"):
        return UnitTestCase(name, parent=collector)
    else:
        return []
