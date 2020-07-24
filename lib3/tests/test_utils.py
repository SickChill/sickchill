from unittest import TestCase

from dogpile import util


class UtilsTest(TestCase):

    """ Test the relevant utils functionality.
    """

    def test_coerce_string_conf(self):
        settings = {"expiration_time": "-1"}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced["expiration_time"], -1)

        settings = {"expiration_time": "+1"}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced["expiration_time"], 1)
        self.assertEqual(type(coerced["expiration_time"]), int)

        settings = {"arguments.lock_sleep": "0.1"}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced["arguments.lock_sleep"], 0.1)

        settings = {"arguments.lock_sleep": "-3.14e-10"}
        coerced = util.coerce_string_conf(settings)
        self.assertEqual(coerced["arguments.lock_sleep"], -3.14e-10)
