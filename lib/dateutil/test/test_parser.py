# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ._common import unittest

from datetime import datetime, timedelta, date

from dateutil.tz import tzoffset
from dateutil.parser import *

from six import assertRaisesRegex, PY3

class ParserTest(unittest.TestCase):

    def setUp(self):
        self.tzinfos = {"BRST": -10800}
        self.brsttz = tzoffset("BRST", -10800)
        self.default = datetime(2003, 9, 25)

        # Parser should be able to handle bytestring and unicode
        base_str = '2014-05-01 08:00:00'
        try:
            # Python 2.x
            self.uni_str = unicode(base_str)
            self.str_str = str(base_str)
        except NameError:
            self.uni_str = str(base_str)
            self.str_str = bytes(base_str.encode())

    def testEmptyString(self):
        with self.assertRaises(ValueError):
            parse('')

    def testDateCommandFormat(self):
        self.assertEqual(parse("Thu Sep 25 10:36:28 BRST 2003",
                               tzinfos=self.tzinfos),
                         datetime(2003, 9, 25, 10, 36, 28,
                                  tzinfo=self.brsttz))

    def testDateCommandFormatUnicode(self):
        self.assertEqual(parse("Thu Sep 25 10:36:28 BRST 2003",
                               tzinfos=self.tzinfos),
                         datetime(2003, 9, 25, 10, 36, 28,
                                  tzinfo=self.brsttz))


    def testDateCommandFormatReversed(self):
        self.assertEqual(parse("2003 10:36:28 BRST 25 Sep Thu",
                               tzinfos=self.tzinfos),
                         datetime(2003, 9, 25, 10, 36, 28,
                                  tzinfo=self.brsttz))

    def testDateCommandFormatWithLong(self):
        if not PY3:
            self.assertEqual(parse("Thu Sep 25 10:36:28 BRST 2003",
                                   tzinfos={"BRST": long(-10800)}),
                             datetime(2003, 9, 25, 10, 36, 28,
                                      tzinfo=self.brsttz))
    def testDateCommandFormatIgnoreTz(self):
        self.assertEqual(parse("Thu Sep 25 10:36:28 BRST 2003",
                               ignoretz=True),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip1(self):
        self.assertEqual(parse("Thu Sep 25 10:36:28 2003"),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip2(self):
        self.assertEqual(parse("Thu Sep 25 10:36:28", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip3(self):
        self.assertEqual(parse("Thu Sep 10:36:28", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip4(self):
        self.assertEqual(parse("Thu 10:36:28", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip5(self):
        self.assertEqual(parse("Sep 10:36:28", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip6(self):
        self.assertEqual(parse("10:36:28", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testDateCommandFormatStrip7(self):
        self.assertEqual(parse("10:36", default=self.default),
                         datetime(2003, 9, 25, 10, 36))

    def testDateCommandFormatStrip8(self):
        self.assertEqual(parse("Thu Sep 25 2003"),
                         datetime(2003, 9, 25))

    def testDateCommandFormatStrip9(self):
        self.assertEqual(parse("Sep 25 2003"),
                         datetime(2003, 9, 25))

    def testDateCommandFormatStrip10(self):
        self.assertEqual(parse("Sep 2003", default=self.default),
                         datetime(2003, 9, 25))

    def testDateCommandFormatStrip11(self):
        self.assertEqual(parse("Sep", default=self.default),
                         datetime(2003, 9, 25))

    def testDateCommandFormatStrip12(self):
        self.assertEqual(parse("2003", default=self.default),
                         datetime(2003, 9, 25))

    def testDateRCommandFormat(self):
        self.assertEqual(parse("Thu, 25 Sep 2003 10:49:41 -0300"),
                         datetime(2003, 9, 25, 10, 49, 41,
                                  tzinfo=self.brsttz))

    def testISOFormat(self):
        self.assertEqual(parse("2003-09-25T10:49:41.5-03:00"),
                         datetime(2003, 9, 25, 10, 49, 41, 500000,
                                  tzinfo=self.brsttz))

    def testISOFormatStrip1(self):
        self.assertEqual(parse("2003-09-25T10:49:41-03:00"),
                         datetime(2003, 9, 25, 10, 49, 41,
                                  tzinfo=self.brsttz))

    def testISOFormatStrip2(self):
        self.assertEqual(parse("2003-09-25T10:49:41"),
                         datetime(2003, 9, 25, 10, 49, 41))

    def testISOFormatStrip3(self):
        self.assertEqual(parse("2003-09-25T10:49"),
                         datetime(2003, 9, 25, 10, 49))

    def testISOFormatStrip4(self):
        self.assertEqual(parse("2003-09-25T10"),
                         datetime(2003, 9, 25, 10))

    def testISOFormatStrip5(self):
        self.assertEqual(parse("2003-09-25"),
                         datetime(2003, 9, 25))

    def testISOStrippedFormat(self):
        self.assertEqual(parse("20030925T104941.5-0300"),
                         datetime(2003, 9, 25, 10, 49, 41, 500000,
                                  tzinfo=self.brsttz))

    def testISOStrippedFormatStrip1(self):
        self.assertEqual(parse("20030925T104941-0300"),
                         datetime(2003, 9, 25, 10, 49, 41,
                                  tzinfo=self.brsttz))

    def testISOStrippedFormatStrip2(self):
        self.assertEqual(parse("20030925T104941"),
                         datetime(2003, 9, 25, 10, 49, 41))

    def testISOStrippedFormatStrip3(self):
        self.assertEqual(parse("20030925T1049"),
                         datetime(2003, 9, 25, 10, 49, 0))

    def testISOStrippedFormatStrip4(self):
        self.assertEqual(parse("20030925T10"),
                         datetime(2003, 9, 25, 10))

    def testISOStrippedFormatStrip5(self):
        self.assertEqual(parse("20030925"),
                         datetime(2003, 9, 25))

    def testPythonLoggerFormat(self):
        self.assertEqual(parse("2003-09-25 10:49:41,502"),
                         datetime(2003, 9, 25, 10, 49, 41, 502000))

    def testNoSeparator1(self):
        self.assertEqual(parse("199709020908"),
                         datetime(1997, 9, 2, 9, 8))

    def testNoSeparator2(self):
        self.assertEqual(parse("19970902090807"),
                         datetime(1997, 9, 2, 9, 8, 7))

    def testDateWithDash1(self):
        self.assertEqual(parse("2003-09-25"),
                         datetime(2003, 9, 25))

    def testDateWithDash2(self):
        self.assertEqual(parse("2003-Sep-25"),
                         datetime(2003, 9, 25))

    def testDateWithDash3(self):
        self.assertEqual(parse("25-Sep-2003"),
                         datetime(2003, 9, 25))

    def testDateWithDash4(self):
        self.assertEqual(parse("25-Sep-2003"),
                         datetime(2003, 9, 25))

    def testDateWithDash5(self):
        self.assertEqual(parse("Sep-25-2003"),
                         datetime(2003, 9, 25))

    def testDateWithDash6(self):
        self.assertEqual(parse("09-25-2003"),
                         datetime(2003, 9, 25))

    def testDateWithDash7(self):
        self.assertEqual(parse("25-09-2003"),
                         datetime(2003, 9, 25))

    def testDateWithDash8(self):
        self.assertEqual(parse("10-09-2003", dayfirst=True),
                         datetime(2003, 9, 10))

    def testDateWithDash9(self):
        self.assertEqual(parse("10-09-2003"),
                         datetime(2003, 10, 9))

    def testDateWithDash10(self):
        self.assertEqual(parse("10-09-03"),
                         datetime(2003, 10, 9))

    def testDateWithDash11(self):
        self.assertEqual(parse("10-09-03", yearfirst=True),
                         datetime(2010, 9, 3))

    def testDateWithDot1(self):
        self.assertEqual(parse("2003.09.25"),
                         datetime(2003, 9, 25))

    def testDateWithDot2(self):
        self.assertEqual(parse("2003.Sep.25"),
                         datetime(2003, 9, 25))

    def testDateWithDot3(self):
        self.assertEqual(parse("25.Sep.2003"),
                         datetime(2003, 9, 25))

    def testDateWithDot4(self):
        self.assertEqual(parse("25.Sep.2003"),
                         datetime(2003, 9, 25))

    def testDateWithDot5(self):
        self.assertEqual(parse("Sep.25.2003"),
                         datetime(2003, 9, 25))

    def testDateWithDot6(self):
        self.assertEqual(parse("09.25.2003"),
                         datetime(2003, 9, 25))

    def testDateWithDot7(self):
        self.assertEqual(parse("25.09.2003"),
                         datetime(2003, 9, 25))

    def testDateWithDot8(self):
        self.assertEqual(parse("10.09.2003", dayfirst=True),
                         datetime(2003, 9, 10))

    def testDateWithDot9(self):
        self.assertEqual(parse("10.09.2003"),
                         datetime(2003, 10, 9))

    def testDateWithDot10(self):
        self.assertEqual(parse("10.09.03"),
                         datetime(2003, 10, 9))

    def testDateWithDot11(self):
        self.assertEqual(parse("10.09.03", yearfirst=True),
                         datetime(2010, 9, 3))

    def testDateWithSlash1(self):
        self.assertEqual(parse("2003/09/25"),
                         datetime(2003, 9, 25))

    def testDateWithSlash2(self):
        self.assertEqual(parse("2003/Sep/25"),
                         datetime(2003, 9, 25))

    def testDateWithSlash3(self):
        self.assertEqual(parse("25/Sep/2003"),
                         datetime(2003, 9, 25))

    def testDateWithSlash4(self):
        self.assertEqual(parse("25/Sep/2003"),
                         datetime(2003, 9, 25))

    def testDateWithSlash5(self):
        self.assertEqual(parse("Sep/25/2003"),
                         datetime(2003, 9, 25))

    def testDateWithSlash6(self):
        self.assertEqual(parse("09/25/2003"),
                         datetime(2003, 9, 25))

    def testDateWithSlash7(self):
        self.assertEqual(parse("25/09/2003"),
                         datetime(2003, 9, 25))

    def testDateWithSlash8(self):
        self.assertEqual(parse("10/09/2003", dayfirst=True),
                         datetime(2003, 9, 10))

    def testDateWithSlash9(self):
        self.assertEqual(parse("10/09/2003"),
                         datetime(2003, 10, 9))

    def testDateWithSlash10(self):
        self.assertEqual(parse("10/09/03"),
                         datetime(2003, 10, 9))

    def testDateWithSlash11(self):
        self.assertEqual(parse("10/09/03", yearfirst=True),
                         datetime(2010, 9, 3))

    def testDateWithSpace1(self):
        self.assertEqual(parse("2003 09 25"),
                         datetime(2003, 9, 25))

    def testDateWithSpace2(self):
        self.assertEqual(parse("2003 Sep 25"),
                         datetime(2003, 9, 25))

    def testDateWithSpace3(self):
        self.assertEqual(parse("25 Sep 2003"),
                         datetime(2003, 9, 25))

    def testDateWithSpace4(self):
        self.assertEqual(parse("25 Sep 2003"),
                         datetime(2003, 9, 25))

    def testDateWithSpace5(self):
        self.assertEqual(parse("Sep 25 2003"),
                         datetime(2003, 9, 25))

    def testDateWithSpace6(self):
        self.assertEqual(parse("09 25 2003"),
                         datetime(2003, 9, 25))

    def testDateWithSpace7(self):
        self.assertEqual(parse("25 09 2003"),
                         datetime(2003, 9, 25))

    def testDateWithSpace8(self):
        self.assertEqual(parse("10 09 2003", dayfirst=True),
                         datetime(2003, 9, 10))

    def testDateWithSpace9(self):
        self.assertEqual(parse("10 09 2003"),
                         datetime(2003, 10, 9))

    def testDateWithSpace10(self):
        self.assertEqual(parse("10 09 03"),
                         datetime(2003, 10, 9))

    def testDateWithSpace11(self):
        self.assertEqual(parse("10 09 03", yearfirst=True),
                         datetime(2010, 9, 3))

    def testDateWithSpace12(self):
        self.assertEqual(parse("25 09 03"),
                         datetime(2003, 9, 25))

    def testStrangelyOrderedDate1(self):
        self.assertEqual(parse("03 25 Sep"),
                         datetime(2003, 9, 25))

    def testStrangelyOrderedDate2(self):
        self.assertEqual(parse("2003 25 Sep"),
                         datetime(2003, 9, 25))

    def testStrangelyOrderedDate3(self):
        self.assertEqual(parse("25 03 Sep"),
                         datetime(2025, 9, 3))

    def testHourWithLetters(self):
        self.assertEqual(parse("10h36m28.5s", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28, 500000))

    def testHourWithLettersStrip1(self):
        self.assertEqual(parse("10h36m28s", default=self.default),
                         datetime(2003, 9, 25, 10, 36, 28))

    def testHourWithLettersStrip2(self):
        self.assertEqual(parse("10h36m", default=self.default),
                         datetime(2003, 9, 25, 10, 36))

    def testHourWithLettersStrip3(self):
        self.assertEqual(parse("10h", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourWithLettersStrip4(self):
        self.assertEqual(parse("10 h 36", default=self.default),
                         datetime(2003, 9, 25, 10, 36))

    def testAMPMNoHour(self):
        with self.assertRaises(ValueError):
            parse("AM")

        with self.assertRaises(ValueError):
            parse("Jan 20, 2015 PM")

    def testHourAmPm1(self):
        self.assertEqual(parse("10h am", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm2(self):
        self.assertEqual(parse("10h pm", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testHourAmPm3(self):
        self.assertEqual(parse("10am", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm4(self):
        self.assertEqual(parse("10pm", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testHourAmPm5(self):
        self.assertEqual(parse("10:00 am", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm6(self):
        self.assertEqual(parse("10:00 pm", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testHourAmPm7(self):
        self.assertEqual(parse("10:00am", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm8(self):
        self.assertEqual(parse("10:00pm", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testHourAmPm9(self):
        self.assertEqual(parse("10:00a.m", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm10(self):
        self.assertEqual(parse("10:00p.m", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testHourAmPm11(self):
        self.assertEqual(parse("10:00a.m.", default=self.default),
                         datetime(2003, 9, 25, 10))

    def testHourAmPm12(self):
        self.assertEqual(parse("10:00p.m.", default=self.default),
                         datetime(2003, 9, 25, 22))

    def testAMPMRange(self):
        with self.assertRaises(ValueError):
            parse("13:44 AM")

        with self.assertRaises(ValueError):
            parse("January 25, 1921 23:13 PM")

    def testPertain(self):
        self.assertEqual(parse("Sep 03", default=self.default),
                         datetime(2003, 9, 3))
        self.assertEqual(parse("Sep of 03", default=self.default),
                         datetime(2003, 9, 25))

    def testWeekdayAlone(self):
        self.assertEqual(parse("Wed", default=self.default),
                         datetime(2003, 10, 1))

    def testLongWeekday(self):
        self.assertEqual(parse("Wednesday", default=self.default),
                         datetime(2003, 10, 1))

    def testLongMonth(self):
        self.assertEqual(parse("October", default=self.default),
                         datetime(2003, 10, 25))

    def testZeroYear(self):
        self.assertEqual(parse("31-Dec-00", default=self.default),
                         datetime(2000, 12, 31))

    def testFuzzy(self):
        s = "Today is 25 of September of 2003, exactly " \
            "at 10:49:41 with timezone -03:00."
        self.assertEqual(parse(s, fuzzy=True),
                         datetime(2003, 9, 25, 10, 49, 41,
                                  tzinfo=self.brsttz))

    def testFuzzyWithTokens(self):
        s = "Today is 25 of September of 2003, exactly " \
            "at 10:49:41 with timezone -03:00."
        self.assertEqual(parse(s, fuzzy_with_tokens=True),
                         (datetime(2003, 9, 25, 10, 49, 41,
                                   tzinfo=self.brsttz),
                         ('Today is ', 'of ', ', exactly at ',
                          ' with timezone ', '.')))

    def testFuzzyAMPMProblem(self):
        # Sometimes fuzzy parsing results in AM/PM flag being set without
        # hours - if it's fuzzy it should ignore that.
        s1 = "I have a meeting on March 1, 1974."
        s2 = "On June 8th, 2020, I am going to be the first man on Mars"

        # Also don't want any erroneous AM or PMs changing the parsed time
        s3 = "Meet me at the AM/PM on Sunset at 3:00 AM on December 3rd, 2003"
        s4 = "Meet me at 3:00AM on December 3rd, 2003 at the AM/PM on Sunset"

        self.assertEqual(parse(s1, fuzzy=True), datetime(1974, 3, 1))
        self.assertEqual(parse(s2, fuzzy=True), datetime(2020, 6, 8))
        self.assertEqual(parse(s3, fuzzy=True), datetime(2003, 12, 3, 3))
        self.assertEqual(parse(s4, fuzzy=True), datetime(2003, 12, 3, 3))

    def testFuzzyIgnoreAMPM(self):
        s1 = "Jan 29, 1945 14:45 AM I going to see you there?"

        self.assertEqual(parse(s1, fuzzy=True), datetime(1945, 1, 29, 14, 45))

    def testExtraSpace(self):
        self.assertEqual(parse("  July   4 ,  1976   12:01:02   am  "),
                         datetime(1976, 7, 4, 0, 1, 2))

    def testRandomFormat1(self):
        self.assertEqual(parse("Wed, July 10, '96"),
                         datetime(1996, 7, 10, 0, 0))

    def testRandomFormat2(self):
        self.assertEqual(parse("1996.07.10 AD at 15:08:56 PDT",
                               ignoretz=True),
                         datetime(1996, 7, 10, 15, 8, 56))

    def testRandomFormat3(self):
        self.assertEqual(parse("1996.July.10 AD 12:08 PM"),
                         datetime(1996, 7, 10, 12, 8))

    def testRandomFormat4(self):
        self.assertEqual(parse("Tuesday, April 12, 1952 AD 3:30:42pm PST",
                               ignoretz=True),
                         datetime(1952, 4, 12, 15, 30, 42))

    def testRandomFormat5(self):
        self.assertEqual(parse("November 5, 1994, 8:15:30 am EST",
                               ignoretz=True),
                         datetime(1994, 11, 5, 8, 15, 30))

    def testRandomFormat6(self):
        self.assertEqual(parse("1994-11-05T08:15:30-05:00",
                               ignoretz=True),
                         datetime(1994, 11, 5, 8, 15, 30))

    def testRandomFormat7(self):
        self.assertEqual(parse("1994-11-05T08:15:30Z",
                               ignoretz=True),
                         datetime(1994, 11, 5, 8, 15, 30))

    def testRandomFormat8(self):
        self.assertEqual(parse("July 4, 1976"), datetime(1976, 7, 4))

    def testRandomFormat9(self):
        self.assertEqual(parse("7 4 1976"), datetime(1976, 7, 4))

    def testRandomFormat10(self):
        self.assertEqual(parse("4 jul 1976"), datetime(1976, 7, 4))

    def testRandomFormat11(self):
        self.assertEqual(parse("7-4-76"), datetime(1976, 7, 4))

    def testRandomFormat12(self):
        self.assertEqual(parse("19760704"), datetime(1976, 7, 4))

    def testRandomFormat13(self):
        self.assertEqual(parse("0:01:02", default=self.default),
                         datetime(2003, 9, 25, 0, 1, 2))

    def testRandomFormat14(self):
        self.assertEqual(parse("12h 01m02s am", default=self.default),
                         datetime(2003, 9, 25, 0, 1, 2))

    def testRandomFormat15(self):
        self.assertEqual(parse("0:01:02 on July 4, 1976"),
                         datetime(1976, 7, 4, 0, 1, 2))

    def testRandomFormat16(self):
        self.assertEqual(parse("0:01:02 on July 4, 1976"),
                         datetime(1976, 7, 4, 0, 1, 2))

    def testRandomFormat17(self):
        self.assertEqual(parse("1976-07-04T00:01:02Z", ignoretz=True),
                         datetime(1976, 7, 4, 0, 1, 2))

    def testRandomFormat18(self):
        self.assertEqual(parse("July 4, 1976 12:01:02 am"),
                         datetime(1976, 7, 4, 0, 1, 2))

    def testRandomFormat19(self):
        self.assertEqual(parse("Mon Jan  2 04:24:27 1995"),
                         datetime(1995, 1, 2, 4, 24, 27))

    def testRandomFormat20(self):
        self.assertEqual(parse("Tue Apr 4 00:22:12 PDT 1995", ignoretz=True),
                         datetime(1995, 4, 4, 0, 22, 12))

    def testRandomFormat21(self):
        self.assertEqual(parse("04.04.95 00:22"),
                         datetime(1995, 4, 4, 0, 22))

    def testRandomFormat22(self):
        self.assertEqual(parse("Jan 1 1999 11:23:34.578"),
                         datetime(1999, 1, 1, 11, 23, 34, 578000))

    def testRandomFormat23(self):
        self.assertEqual(parse("950404 122212"),
                         datetime(1995, 4, 4, 12, 22, 12))

    def testRandomFormat24(self):
        self.assertEqual(parse("0:00 PM, PST", default=self.default,
                               ignoretz=True),
                         datetime(2003, 9, 25, 12, 0))

    def testRandomFormat25(self):
        self.assertEqual(parse("12:08 PM", default=self.default),
                         datetime(2003, 9, 25, 12, 8))

    def testRandomFormat26(self):
        self.assertEqual(parse("5:50 A.M. on June 13, 1990"),
                         datetime(1990, 6, 13, 5, 50))

    def testRandomFormat27(self):
        self.assertEqual(parse("3rd of May 2001"), datetime(2001, 5, 3))

    def testRandomFormat28(self):
        self.assertEqual(parse("5th of March 2001"), datetime(2001, 3, 5))

    def testRandomFormat29(self):
        self.assertEqual(parse("1st of May 2003"), datetime(2003, 5, 1))

    def testRandomFormat30(self):
        self.assertEqual(parse("01h02m03", default=self.default),
                         datetime(2003, 9, 25, 1, 2, 3))

    def testRandomFormat31(self):
        self.assertEqual(parse("01h02", default=self.default),
                         datetime(2003, 9, 25, 1, 2))

    def testRandomFormat32(self):
        self.assertEqual(parse("01h02s", default=self.default),
                         datetime(2003, 9, 25, 1, 0, 2))

    def testRandomFormat33(self):
        self.assertEqual(parse("01m02", default=self.default),
                         datetime(2003, 9, 25, 0, 1, 2))

    def testRandomFormat34(self):
        self.assertEqual(parse("01m02h", default=self.default),
                         datetime(2003, 9, 25, 2, 1))

    def testRandomFormat35(self):
        self.assertEqual(parse("2004 10 Apr 11h30m", default=self.default),
                         datetime(2004, 4, 10, 11, 30))

    def test_99_ad(self):
        self.assertEqual(parse('0099-01-01T00:00:00'),
                         datetime(99, 1, 1, 0, 0))

    def test_31_ad(self):
        self.assertEqual(parse('0031-01-01T00:00:00'),
                         datetime(31, 1, 1, 0, 0))

    def testInvalidDay(self):
        with self.assertRaises(ValueError):
            parse("Feb 30, 2007")

    def testUnspecifiedDayFallback(self):
        # Test that for an unspecified day, the fallback behavior is correct.
        self.assertEqual(parse("April 2009", default=datetime(2010, 1, 31)),
                         datetime(2009, 4, 30))

    def testUnspecifiedDayFallbackFebNoLeapYear(self):        
        self.assertEqual(parse("Feb 2007", default=datetime(2010, 1, 31)),
                         datetime(2007, 2, 28))

    def testUnspecifiedDayFallbackFebLeapYear(self):        
        self.assertEqual(parse("Feb 2008", default=datetime(2010, 1, 31)),
                         datetime(2008, 2, 29))

    def testErrorType01(self):
        self.assertRaises(ValueError,
                          parse, 'shouldfail')

    def testCorrectErrorOnFuzzyWithTokens(self):
        assertRaisesRegex(self, ValueError, 'Unknown string format',
                          parse, '04/04/32/423', fuzzy_with_tokens=True)
        assertRaisesRegex(self, ValueError, 'Unknown string format',
                          parse, '04/04/04 +32423', fuzzy_with_tokens=True)
        assertRaisesRegex(self, ValueError, 'Unknown string format',
                          parse, '04/04/0d4', fuzzy_with_tokens=True)

    def testIncreasingCTime(self):
        # This test will check 200 different years, every month, every day,
        # every hour, every minute, every second, and every weekday, using
        # a delta of more or less 1 year, 1 month, 1 day, 1 minute and
        # 1 second.
        delta = timedelta(days=365+31+1, seconds=1+60+60*60)
        dt = datetime(1900, 1, 1, 0, 0, 0, 0)
        for i in range(200):
            self.assertEqual(parse(dt.ctime()), dt)
            dt += delta

    def testIncreasingISOFormat(self):
        delta = timedelta(days=365+31+1, seconds=1+60+60*60)
        dt = datetime(1900, 1, 1, 0, 0, 0, 0)
        for i in range(200):
            self.assertEqual(parse(dt.isoformat()), dt)
            dt += delta

    def testMicrosecondsPrecisionError(self):
        # Skip found out that sad precision problem. :-(
        dt1 = parse("00:11:25.01")
        dt2 = parse("00:12:10.01")
        self.assertEqual(dt1.microsecond, 10000)
        self.assertEqual(dt2.microsecond, 10000)

    def testMicrosecondPrecisionErrorReturns(self):
        # One more precision issue, discovered by Eric Brown.  This should
        # be the last one, as we're no longer using floating points.
        for ms in [100001, 100000, 99999, 99998,
                    10001,  10000,  9999,  9998,
                     1001,   1000,   999,   998,
                      101,    100,    99,    98]:
            dt = datetime(2008, 2, 27, 21, 26, 1, ms)
            self.assertEqual(parse(dt.isoformat()), dt)

    def testHighPrecisionSeconds(self):
        self.assertEqual(parse("20080227T21:26:01.123456789"),
                          datetime(2008, 2, 27, 21, 26, 1, 123456))

    def testCustomParserInfo(self):
        # Custom parser info wasn't working, as Michael Elsdörfer discovered.
        from dateutil.parser import parserinfo, parser

        class myparserinfo(parserinfo):
            MONTHS = parserinfo.MONTHS[:]
            MONTHS[0] = ("Foo", "Foo")
        myparser = parser(myparserinfo())
        dt = myparser.parse("01/Foo/2007")
        self.assertEqual(dt, datetime(2007, 1, 1))

    def testParseStr(self):
        self.assertEqual(parse(self.str_str),
                         parse(self.uni_str))

    def testParserParseStr(self):
        from dateutil.parser import parser

        self.assertEqual(parser().parse(self.str_str),
                         parser().parse(self.uni_str))

    def testParseUnicodeWords(self):

        class rus_parserinfo(parserinfo):
            MONTHS = [("янв", "Январь"),
                      ("фев", "Февраль"),
                      ("мар", "Март"),
                      ("апр", "Апрель"),
                      ("май", "Май"),
                      ("июн", "Июнь"),
                      ("июл", "Июль"),
                      ("авг", "Август"),
                      ("сен", "Сентябрь"),
                      ("окт", "Октябрь"),
                      ("ноя", "Ноябрь"),
                      ("дек", "Декабрь")]

        self.assertEqual(parse('10 Сентябрь 2015 10:20',
                               parserinfo=rus_parserinfo()),
                         datetime(2015, 9, 10, 10, 20))

    def testParseWithNulls(self):
        # This relies on the from __future__ import unicode_literals, because
        # explicitly specifying a unicode literal is a syntax error in Py 3.2
        # May want to switch to u'...' if we ever drop Python 3.2 support.
        pstring = '\x00\x00August 29, 1924'

        self.assertEqual(parse(pstring),
                         datetime(1924, 8, 29))

