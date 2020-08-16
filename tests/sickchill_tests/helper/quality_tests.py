

"""
Test qualities
"""

import unittest

from sickchill.helper.quality import get_quality_string
from sickchill.oldbeard.common import ANY, HD, HD720p, HD1080p, Quality, SD


class QualityTests(unittest.TestCase):
    """
    Test qualities
    """
    def test_get_quality_string(self):
        """
        Test get quality string
        """
        tests = {
            ANY: 'Any',
            HD: 'HD',
            HD720p: 'HD720p',
            HD1080p: 'HD1080p',
            Quality.FULLHDBLURAY: '1080p BluRay',
            Quality.FULLHDTV: '1080p HDTV',
            Quality.FULLHDWEBDL: '1080p WEB-DL',
            Quality.HDBLURAY: '720p BluRay',
            Quality.HDTV: '720p HDTV',
            Quality.HDWEBDL: '720p WEB-DL',
            Quality.NONE: 'N/A',
            Quality.RAWHDTV: 'RawHD',
            Quality.SDDVD: 'SD DVD',
            Quality.SDTV: 'SDTV',
            Quality.UNKNOWN: 'Unknown',
            SD: 'SD',
            1000000: 'Custom',  # An invalid quality number to test the default case
        }

        for (quality, result) in tests.items():
            self.assertEqual(get_quality_string(quality), result)


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(QualityTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
