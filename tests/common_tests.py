# coding=utf-8

"""
Unit Tests for sickbeard/common.py
"""

import sys
import os.path
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import common


class QualityTests(unittest.TestCase):
    """
    Test Case for common.Quality
    """

    # TODO: repack / proper ? air-by-date ? season rip? multi-ep?

    def test_SDTV(self):
        """
        Test SDTV against nameQuality
        """
        tests = [
            "Test.Show.S01E02.PDTV.XViD-GROUP",
            "Test.Show.S01E02.PDTV.x264-GROUP",
            "Test.Show.S01E02.HDTV.XViD-GROUP",
            "Test.Show.S01E02.HDTV.x264-GROUP",
            "Test.Show.S01E02.DSR.XViD-GROUP",
            "Test.Show.S01E02.DSR.x264-GROUP",
            "Test.Show.S01E02.TVRip.XViD-GROUP",
            "Test.Show.S01E02.TVRip.x264-GROUP",
            "Test.Show.S01E02.WEBRip.XViD-GROUP",
            "Test.Show.S01E02.WEBRip.x264-GROUP",
            "Test.Show.S01E02.WEB-DL.x264-GROUP",
            "Test.Show.S01E02.WEB-DL.AAC2.0.H.264-GROUP",
            "Test.Show.S01E02 WEB-DL H 264-GROUP",
            "Test.Show.S01E02_WEB-DL_H_264-GROUP",
            "Test.Show.S01E02.WEB-DL.AAC2.0.H264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.SDTV, common.Quality.nameQuality(test))

    def test_SDDVD(self):
        """
        Test SDDVD against nameQuality
        """
        tests = [
            "Test.Show.S01E02.DVDRiP.XViD-GROUP",
            "Test.Show.S01E02.DVDRiP.DiVX-GROUP",
            "Test.Show.S01E02.DVDRiP.x264-GROUP",
            "Test.Show.S01E02.DVDRip.WS.XViD-GROUP",
            "Test.Show.S01E02.DVDRip.WS.DiVX-GROUP",
            "Test.Show.S01E02.DVDRip.WS.x264-GROUP",
            "Test.Show.S01E02.BDRIP.XViD-GROUP",
            "Test.Show.S01E02.BDRIP.DiVX-GROUP",
            "Test.Show.S01E02.BDRIP.x264-GROUP",
            "Test.Show.S01E02.BDRIP.WS.XViD-GROUP",
            "Test.Show.S01E02.BDRIP.WS.DiVX-GROUP",
            "Test.Show.S01E02.BDRIP.WS.x264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.SDDVD, common.Quality.nameQuality(test))

    def test_HDTV(self):
        """
        Test HDTV against nameQuality
        """
        tests = [
            "Test.Show.S01E02.720p.HDTV.x264-GROUP",
            "Test.Show.S01E02.HR.WS.PDTV.x264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.HDTV, common.Quality.nameQuality(test))

    def test_RAWHDTV(self):
        """
        Test RAWHDTV against nameQuality
        """
        tests = [
            "Test.Show.S01E02.720p.HDTV.DD5.1.MPEG2-GROUP",
            "Test.Show.S01E02.1080i.HDTV.DD2.0.MPEG2-GROUP",
            "Test.Show.S01E02.1080i.HDTV.H.264.DD2.0-GROUP",
            "Test Show - S01E02 - 1080i HDTV MPA1.0 H.264 - GROUP",
            "Test.Show.S01E02.1080i.HDTV.DD.5.1.h264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.RAWHDTV, common.Quality.nameQuality(test))

    def test_FULLHDTV(self):
        """
        Test FULLHDTV against nameQuality
        """
        tests = [
            "Test.Show.S01E02.1080p.HDTV.x264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.FULLHDTV, common.Quality.nameQuality(test))

    def test_HDWEBDL(self):
        """
        Test HDWEBDL against nameQuality
        """
        tests = [
            "Test.Show.S01E02.720p.WEB-DL-GROUP",
            "Test.Show.S01E02.720p.WEBRip-GROUP",
            "Test.Show.S01E02.WEBRip.720p.H.264.AAC.2.0-GROUP",
            "Test.Show.S01E02.720p.WEB-DL.AAC2.0.H.264-GROUP",
            "Test Show S01E02 720p WEB-DL AAC2 0 H 264-GROUP",
            "Test_Show.S01E02_720p_WEB-DL_AAC2.0_H264-GROUP",
            "Test.Show.S01E02.720p.WEB-DL.AAC2.0.H264-GROUP",
            "Test.Show.S01E02.720p.iTunes.Rip.H264.AAC-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.HDWEBDL, common.Quality.nameQuality(test))

    def test_FULLHDWEBDL(self):
        """
        Test FULLHDWEBDL against nameQuality
        """
        tests = [
            "Test.Show.S01E02.1080p.WEB-DL-GROUP",
            "Test.Show.S01E02.1080p.WEBRip-GROUP",
            "Test.Show.S01E02.WEBRip.1080p.H.264.AAC.2.0-GROUP",
            "Test.Show.S01E02.WEBRip.1080p.H264.AAC.2.0-GROUP",
            "Test.Show.S01E02.1080p.iTunes.H.264.AAC-GROUP",
            "Test Show S01E02 1080p iTunes H 264 AAC-GROUP",
            "Test_Show_S01E02_1080p_iTunes_H_264_AAC-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.FULLHDWEBDL, common.Quality.nameQuality(test))

    def test_HDBLURAY(self):
        """
        Test HDBLURAY against nameQuality
        """
        tests = [
            "Test.Show.S01E02.720p.BluRay.x264-GROUP",
            "Test.Show.S01E02.720p.HDDVD.x264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.HDBLURAY, common.Quality.nameQuality(test))

    def test_FULLHDBLURAY(self):
        """
        Test FULLHDBLURAY against nameQuality
        """
        tests = [
            "Test.Show.S01E02.1080p.BluRay.x264-GROUP",
            "Test.Show.S01E02.1080p.HDDVD.x264-GROUP",
        ]
        for test in tests:
            self.assertEqual(common.Quality.FULLHDBLURAY, common.Quality.nameQuality(test))

    def test_UNKNOWN(self):
        """
        Test UNKNOWN against nameQuality
        """
        tests = [
            "Test.Show.S01E02-SiCKBEARD",
        ]
        for test in tests:
            self.assertEqual(common.Quality.UNKNOWN, common.Quality.nameQuality(test))

    @unittest.expectedFailure
    # reverse parsing does not work
    def test_reverse_parsing(self):
        """
        Test reverse parsing for all qualities
        """
        tests = [
            (common.Quality.SDTV, "Test Show - S01E02 - SDTV - GROUP"),
            (common.Quality.SDDVD, "Test Show - S01E02 - SD DVD - GROUP"),
            (common.Quality.HDTV, "Test Show - S01E02 - HDTV - GROUP"),
            (common.Quality.RAWHDTV, "Test Show - S01E02 - RawHD - GROUP"),
            (common.Quality.FULLHDTV, "Test Show - S01E02 - 1080p HDTV - GROUP"),
            (common.Quality.HDWEBDL, "Test Show - S01E02 - 720p WEB-DL - GROUP"),
            (common.Quality.FULLHDWEBDL, "Test Show - S01E02 - 1080p WEB-DL - GROUP"),
            (common.Quality.HDBLURAY, "Test Show - S01E02 - 720p BluRay - GROUP"),
            (common.Quality.FULLHDBLURAY, "Test Show - S01E02 - 1080p BluRay - GROUP"),
            (common.Quality.UNKNOWN, "Test Show - S01E02 - Unknown - SiCKBEARD"),
        ]
        for test in tests:
            quality, test = test
            self.assertEqual(quality, common.Quality.nameQuality(test),
                             (quality, common.Quality.nameQuality(test), test))


class StatusStringsTest(unittest.TestCase):
    """
    Test Case for common.StatusStrings
    """
    # TODO: Split tests into separate tests and add additional tests

    # Until .has_key() is removed from SickRage, we will test that it still works as expected
    # pylint disable:W0402
    # Use of a deprecated module
    def test_all(self):
        """
        Run all status strings tests
        """
        status_strings = common.statusStrings

        valid = 1, 112, '1', '112'
        unused = 122, 99998989899878676, '99998989899878676', None
        invalid = 'Elephant', (4, 1), [1, 233, 4, None]

        for i in valid:
            self.assertTrue(i in status_strings)

        for i in unused:
            self.assertFalse(i in status_strings)
            with self.assertRaises(KeyError):
                self.assertTrue(status_strings[i])

        for i in status_strings:
            self.assertEqual(status_strings[i], status_strings[str(i)])
            self.assertEqual(i in status_strings, str(i) in status_strings)
            self.assertEqual(status_strings.has_key(i), status_strings.has_key(str(i)))
            self.assertEqual(i in status_strings, status_strings.has_key(i))

        for i in status_strings.qualities:
            self.assertEqual(status_strings[i], status_strings[str(i)])
            self.assertEqual(i in status_strings, str(i) in status_strings)
            self.assertEqual(status_strings.has_key(i), status_strings.has_key(str(i)))
            self.assertEqual(i in status_strings, status_strings.has_key(i))

        for i in invalid:
            with self.assertRaises(TypeError):
                status_strings[i] = 1

        for i in unused:
            if i is None:
                with self.assertRaises(TypeError):
                    status_strings[str(i)] = 1  # 'None' != None
                status_strings[i] = 1  # ...but None can still be used as a key
            else:
                status_strings[str(i)] = 1
            self.assertEqual(status_strings[i], 1)

if __name__ == '__main__':
    print "======================="
    print "STARTING - COMMON TESTS"
    print "======================="

    suite = unittest.TestLoader().loadTestsFromTestCase(QualityTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(StatusStringsTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
