# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ._common import unittest, WarningTestMixin

import calendar
from datetime import datetime, date

from dateutil.relativedelta import *

class RelativeDeltaTest(WarningTestMixin, unittest.TestCase):
    now = datetime(2003, 9, 17, 20, 54, 47, 282310)
    today = date(2003, 9, 17)

    def testInheritance(self):
        # Ensure that relativedelta is inheritance-friendly.
        class rdChildClass(relativedelta):
            pass

        ccRD = rdChildClass(years=1, months=1, days=1, leapdays=1, weeks=1,
                            hours=1, minutes=1, seconds=1, microseconds=1)

        rd = relativedelta(years=1, months=1, days=1, leapdays=1, weeks=1,
                           hours=1, minutes=1, seconds=1, microseconds=1)

        self.assertEqual(type(ccRD + rd), type(ccRD),
                         msg='Addition does not inherit type.')

        self.assertEqual(type(ccRD - rd), type(ccRD),
                         msg='Subtraction does not inherit type.')

        self.assertEqual(type(-ccRD), type(ccRD),
                         msg='Negation does not inherit type.')

        self.assertEqual(type(ccRD * 5.0), type(ccRD),
                         msg='Multiplication does not inherit type.')
        
        self.assertEqual(type(ccRD / 5.0), type(ccRD),
                         msg='Division does not inherit type.')

    def testMonthEndMonthBeginning(self):
        self.assertEqual(relativedelta(datetime(2003, 1, 31, 23, 59, 59),
                                       datetime(2003, 3, 1, 0, 0, 0)),
                         relativedelta(months=-1, seconds=-1))

        self.assertEqual(relativedelta(datetime(2003, 3, 1, 0, 0, 0),
                                       datetime(2003, 1, 31, 23, 59, 59)),
                         relativedelta(months=1, seconds=1))

    def testMonthEndMonthBeginningLeapYear(self):
        self.assertEqual(relativedelta(datetime(2012, 1, 31, 23, 59, 59),
                                       datetime(2012, 3, 1, 0, 0, 0)),
                         relativedelta(months=-1, seconds=-1))

        self.assertEqual(relativedelta(datetime(2003, 3, 1, 0, 0, 0),
                                       datetime(2003, 1, 31, 23, 59, 59)),
                         relativedelta(months=1, seconds=1))

    def testNextMonth(self):
        self.assertEqual(self.now+relativedelta(months=+1),
                         datetime(2003, 10, 17, 20, 54, 47, 282310))

    def testNextMonthPlusOneWeek(self):
        self.assertEqual(self.now+relativedelta(months=+1, weeks=+1),
                         datetime(2003, 10, 24, 20, 54, 47, 282310))

    def testNextMonthPlusOneWeek10am(self):
        self.assertEqual(self.today +
                         relativedelta(months=+1, weeks=+1, hour=10),
                         datetime(2003, 10, 24, 10, 0))

    def testNextMonthPlusOneWeek10amDiff(self):
        self.assertEqual(relativedelta(datetime(2003, 10, 24, 10, 0),
                                       self.today),
                         relativedelta(months=+1, days=+7, hours=+10))

    def testOneMonthBeforeOneYear(self):
        self.assertEqual(self.now+relativedelta(years=+1, months=-1),
                         datetime(2004, 8, 17, 20, 54, 47, 282310))

    def testMonthsOfDiffNumOfDays(self):
        self.assertEqual(date(2003, 1, 27)+relativedelta(months=+1),
                         date(2003, 2, 27))
        self.assertEqual(date(2003, 1, 31)+relativedelta(months=+1),
                         date(2003, 2, 28))
        self.assertEqual(date(2003, 1, 31)+relativedelta(months=+2),
                         date(2003, 3, 31))

    def testMonthsOfDiffNumOfDaysWithYears(self):
        self.assertEqual(date(2000, 2, 28)+relativedelta(years=+1),
                         date(2001, 2, 28))
        self.assertEqual(date(2000, 2, 29)+relativedelta(years=+1),
                         date(2001, 2, 28))

        self.assertEqual(date(1999, 2, 28)+relativedelta(years=+1),
                         date(2000, 2, 28))
        self.assertEqual(date(1999, 3, 1)+relativedelta(years=+1),
                         date(2000, 3, 1))
        self.assertEqual(date(1999, 3, 1)+relativedelta(years=+1),
                         date(2000, 3, 1))

        self.assertEqual(date(2001, 2, 28)+relativedelta(years=-1),
                         date(2000, 2, 28))
        self.assertEqual(date(2001, 3, 1)+relativedelta(years=-1),
                         date(2000, 3, 1))

    def testNextFriday(self):
        self.assertEqual(self.today+relativedelta(weekday=FR),
                         date(2003, 9, 19))

    def testNextFridayInt(self):
        self.assertEqual(self.today+relativedelta(weekday=calendar.FRIDAY),
                         date(2003, 9, 19))

    def testLastFridayInThisMonth(self):
        self.assertEqual(self.today+relativedelta(day=31, weekday=FR(-1)),
                         date(2003, 9, 26))

    def testNextWednesdayIsToday(self):
        self.assertEqual(self.today+relativedelta(weekday=WE),
                         date(2003, 9, 17))

    def testNextWenesdayNotToday(self):
        self.assertEqual(self.today+relativedelta(days=+1, weekday=WE),
                         date(2003, 9, 24))

    def test15thISOYearWeek(self):
        self.assertEqual(date(2003, 1, 1) +
                         relativedelta(day=4, weeks=+14, weekday=MO(-1)),
                         date(2003, 4, 7))

    def testMillenniumAge(self):
        self.assertEqual(relativedelta(self.now, date(2001, 1, 1)),
                         relativedelta(years=+2, months=+8, days=+16,
                                       hours=+20, minutes=+54, seconds=+47,
                                       microseconds=+282310))

    def testJohnAge(self):
        self.assertEqual(relativedelta(self.now,
                                       datetime(1978, 4, 5, 12, 0)),
                         relativedelta(years=+25, months=+5, days=+12,
                                       hours=+8, minutes=+54, seconds=+47,
                                       microseconds=+282310))

    def testJohnAgeWithDate(self):
        self.assertEqual(relativedelta(self.today,
                                       datetime(1978, 4, 5, 12, 0)),
                         relativedelta(years=+25, months=+5, days=+11,
                                       hours=+12))

    def testYearDay(self):
        self.assertEqual(date(2003, 1, 1)+relativedelta(yearday=260),
                         date(2003, 9, 17))
        self.assertEqual(date(2002, 1, 1)+relativedelta(yearday=260),
                         date(2002, 9, 17))
        self.assertEqual(date(2000, 1, 1)+relativedelta(yearday=260),
                         date(2000, 9, 16))
        self.assertEqual(self.today+relativedelta(yearday=261),
                         date(2003, 9, 18))

    def testYearDayBug(self):
        # Tests a problem reported by Adam Ryan.
        self.assertEqual(date(2010, 1, 1)+relativedelta(yearday=15),
                         date(2010, 1, 15))

    def testNonLeapYearDay(self):
        self.assertEqual(date(2003, 1, 1)+relativedelta(nlyearday=260),
                         date(2003, 9, 17))
        self.assertEqual(date(2002, 1, 1)+relativedelta(nlyearday=260),
                         date(2002, 9, 17))
        self.assertEqual(date(2000, 1, 1)+relativedelta(nlyearday=260),
                         date(2000, 9, 17))
        self.assertEqual(self.today+relativedelta(yearday=261),
                         date(2003, 9, 18))

    def testAddition(self):
        self.assertEqual(relativedelta(days=10) +
                         relativedelta(years=1, months=2, days=3, hours=4,
                                       minutes=5, microseconds=6),
                         relativedelta(years=1, months=2, days=13, hours=4,
                                       minutes=5, microseconds=6))

    def testAdditionToDatetime(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=1),
                         datetime(2000, 1, 2))

    def testRightAdditionToDatetime(self):
        self.assertEqual(relativedelta(days=1) + datetime(2000, 1, 1),
                         datetime(2000, 1, 2))

    def testAdditionInvalidType(self):
        with self.assertRaises(TypeError):
            relativedelta(days=3) + 9

    def testSubtraction(self):
        self.assertEqual(relativedelta(days=10) -
                         relativedelta(years=1, months=2, days=3, hours=4,
                                       minutes=5, microseconds=6),
                         relativedelta(years=-1, months=-2, days=7, hours=-4,
                                       minutes=-5, microseconds=-6))

    def testRightSubtractionFromDatetime(self):
        self.assertEqual(datetime(2000, 1, 2) - relativedelta(days=1),
                         datetime(2000, 1, 1))

    def testSubractionWithDatetime(self):
        self.assertRaises(TypeError, lambda x, y: x - y,
                          (relativedelta(days=1), datetime(2000, 1, 1)))

    def testSubtractionInvalidType(self):
        with self.assertRaises(TypeError):
            relativedelta(hours=12) - 14

    def testMultiplication(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=1) * 28,
                         datetime(2000, 1, 29))
        self.assertEqual(datetime(2000, 1, 1) + 28 * relativedelta(days=1),
                         datetime(2000, 1, 29))

    def testDivision(self):
        self.assertEqual(datetime(2000, 1, 1) + relativedelta(days=28) / 28,
                         datetime(2000, 1, 2))

    def testBoolean(self):
        self.assertFalse(relativedelta(days=0))
        self.assertTrue(relativedelta(days=1))

    def testComparison(self):
        d1 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, 
                           minutes=1, seconds=1, microseconds=1)
        d2 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, 
                           minutes=1, seconds=1, microseconds=1)
        d3 = relativedelta(years=1, months=1, days=1, leapdays=0, hours=1, 
                           minutes=1, seconds=1, microseconds=2)

        self.assertEqual(d1, d2)
        self.assertNotEqual(d1, d3)

    def testInequalityTypeMismatch(self):
        # Different type
        self.assertFalse(relativedelta(year=1) == 19)

    def testInequalityWeekdays(self):
        # Different weekdays
        no_wday = relativedelta(year=1997, month=4)
        wday_mo_1 = relativedelta(year=1997, month=4, weekday=MO(+1))
        wday_mo_2 = relativedelta(year=1997, month=4, weekday=MO(+2))
        wday_tu = relativedelta(year=1997, month=4, weekday=TU)
        
        self.assertTrue(wday_mo_1 == wday_mo_1)
        
        self.assertFalse(no_wday == wday_mo_1)
        self.assertFalse(wday_mo_1 == no_wday)

        self.assertFalse(wday_mo_1 == wday_mo_2)
        self.assertFalse(wday_mo_2 == wday_mo_1)
       
        self.assertFalse(wday_mo_1 == wday_tu)
        self.assertFalse(wday_tu == wday_mo_1)

    def testMonthOverflow(self):
        self.assertEqual(relativedelta(months=273),
                         relativedelta(years=22, months=9))

    def testWeeks(self):
        # Test that the weeks property is working properly.
        rd = relativedelta(years=4, months=2, weeks=8, days=6)
        self.assertEqual((rd.weeks, rd.days), (8, 8 * 7 + 6))
        
        rd.weeks = 3
        self.assertEqual((rd.weeks, rd.days), (3, 3 * 7 + 6))

    def testRelativeDeltaRepr(self):
        self.assertEqual(repr(relativedelta(years=1, months=-1, days=15)),
                         'relativedelta(years=+1, months=-1, days=+15)')

        self.assertEqual(repr(relativedelta(months=14, seconds=-25)),
                         'relativedelta(years=+1, months=+2, seconds=-25)')

        self.assertEqual(repr(relativedelta(month=3, hour=3, weekday=SU(3))),
                         'relativedelta(month=3, weekday=SU(+3), hour=3)')

    def testRelativeDeltaFractionalYear(self):
        with self.assertRaises(ValueError):
            relativedelta(years=1.5)

    def testRelativeDeltaFractionalMonth(self):
        with self.assertRaises(ValueError):
            relativedelta(months=1.5)

    def testRelativeDeltaFractionalAbsolutes(self):
        # Fractional absolute values will soon be unsupported,
        # check for the deprecation warning.
        with self.assertWarns(DeprecationWarning):
            relativedelta(year=2.86)
        
        with self.assertWarns(DeprecationWarning):
            relativedelta(month=1.29)

        with self.assertWarns(DeprecationWarning):
            relativedelta(day=0.44)

        with self.assertWarns(DeprecationWarning):
            relativedelta(hour=23.98)

        with self.assertWarns(DeprecationWarning):
            relativedelta(minute=45.21)

        with self.assertWarns(DeprecationWarning):
            relativedelta(second=13.2)

        with self.assertWarns(DeprecationWarning):
            relativedelta(microsecond=157221.93)

    def testRelativeDeltaFractionalRepr(self):
        rd = relativedelta(years=3, months=-2, days=1.25)

        self.assertEqual(repr(rd),
                         'relativedelta(years=+3, months=-2, days=+1.25)')

        rd = relativedelta(hours=0.5, seconds=9.22)
        self.assertEqual(repr(rd),
                         'relativedelta(hours=+0.5, seconds=+9.22)')

    def testRelativeDeltaFractionalWeeks(self):
        # Equivalent to days=8, hours=18
        rd = relativedelta(weeks=1.25)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd,
                         datetime(2009, 9, 11, 18))

    def testRelativeDeltaFractionalDays(self):
        rd1 = relativedelta(days=1.48)

        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd1,
                         datetime(2009, 9, 4, 11, 31, 12))

        rd2 = relativedelta(days=1.5)
        self.assertEqual(d1 + rd2,
                         datetime(2009, 9, 4, 12, 0, 0))

    def testRelativeDeltaFractionalHours(self):
        rd = relativedelta(days=1, hours=12.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd,
                         datetime(2009, 9, 4, 12, 30, 0))

    def testRelativeDeltaFractionalMinutes(self):
        rd = relativedelta(hours=1, minutes=30.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd,
                         datetime(2009, 9, 3, 1, 30, 30))

    def testRelativeDeltaFractionalSeconds(self):
        rd = relativedelta(hours=5, minutes=30, seconds=30.5)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd,
                         datetime(2009, 9, 3, 5, 30, 30, 500000))

    def testRelativeDeltaFractionalPositiveOverflow(self):
        # Equivalent to (days=1, hours=14)
        rd1 = relativedelta(days=1.5, hours=2)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd1,
                         datetime(2009, 9, 4, 14, 0, 0))

        # Equivalent to (days=1, hours=14, minutes=45)
        rd2 = relativedelta(days=1.5, hours=2.5, minutes=15)
        d1 = datetime(2009, 9, 3, 0, 0)
        self.assertEqual(d1 + rd2,
                         datetime(2009, 9, 4, 14, 45))

        # Carry back up - equivalent to (days=2, hours=2, minutes=0, seconds=1)
        rd3 = relativedelta(days=1.5, hours=13, minutes=59.5, seconds=31)
        self.assertEqual(d1 + rd3,
                         datetime(2009, 9, 5, 2, 0, 1))

    def testRelativeDeltaFractionalNegativeDays(self):
        # Equivalent to (days=-1, hours=-1)
        rd1 = relativedelta(days=-1.5, hours=11)
        d1 = datetime(2009, 9, 3, 12, 0)
        self.assertEqual(d1 + rd1,
                         datetime(2009, 9, 2, 11, 0, 0))

        # Equivalent to (days=-1, hours=-9)
        rd2 = relativedelta(days=-1.25, hours=-3)
        self.assertEqual(d1 + rd2,
            datetime(2009, 9, 2, 3))

    def testRelativeDeltaNormalizeFractionalDays(self):
        # Equivalent to (days=2, hours=18)
        rd1 = relativedelta(days=2.75)

        self.assertEqual(rd1.normalized(), relativedelta(days=2, hours=18))

        # Equvalent to (days=1, hours=11, minutes=31, seconds=12)
        rd2 = relativedelta(days=1.48)

        self.assertEqual(rd2.normalized(),
            relativedelta(days=1, hours=11, minutes=31, seconds=12))

    def testRelativeDeltaNormalizeFractionalDays(self):
        # Equivalent to (hours=1, minutes=30)
        rd1 = relativedelta(hours=1.5)

        self.assertEqual(rd1.normalized(), relativedelta(hours=1, minutes=30))

        # Equivalent to (hours=3, minutes=17, seconds=5, microseconds=100)
        rd2 = relativedelta(hours=3.28472225)

        self.assertEqual(rd2.normalized(),
            relativedelta(hours=3, minutes=17, seconds=5, microseconds=100))

    def testRelativeDeltaNormalizeFractionalMinutes(self):
        # Equivalent to (minutes=15, seconds=36)
        rd1 = relativedelta(minutes=15.6)

        self.assertEqual(rd1.normalized(),
            relativedelta(minutes=15, seconds=36))

        # Equivalent to (minutes=25, seconds=20, microseconds=25000)
        rd2 = relativedelta(minutes=25.33375)

        self.assertEqual(rd2.normalized(),
            relativedelta(minutes=25, seconds=20, microseconds=25000))

    def testRelativeDeltaNormalizeFractionalSeconds(self):
        # Equivalent to (seconds=45, microseconds=25000)
        rd1 = relativedelta(seconds=45.025)
        self.assertEqual(rd1.normalized(),
            relativedelta(seconds=45, microseconds=25000))

    def testRelativeDeltaFractionalPositiveOverflow(self):
        # Equivalent to (days=1, hours=14)
        rd1 = relativedelta(days=1.5, hours=2)
        self.assertEqual(rd1.normalized(),
            relativedelta(days=1, hours=14))

        # Equivalent to (days=1, hours=14, minutes=45)
        rd2 = relativedelta(days=1.5, hours=2.5, minutes=15)
        self.assertEqual(rd2.normalized(),
            relativedelta(days=1, hours=14, minutes=45))

        # Carry back up - equivalent to:
        # (days=2, hours=2, minutes=0, seconds=2, microseconds=3)
        rd3 = relativedelta(days=1.5, hours=13, minutes=59.50045,
                            seconds=31.473, microseconds=500003)
        self.assertEqual(rd3.normalized(),
            relativedelta(days=2, hours=2, minutes=0,
                          seconds=2, microseconds=3))

    def testRelativeDeltaFractionalNegativeOverflow(self):
        # Equivalent to (days=-1)
        rd1 = relativedelta(days=-0.5, hours=-12)
        self.assertEqual(rd1.normalized(),
            relativedelta(days=-1))

        # Equivalent to (days=-1)
        rd2 = relativedelta(days=-1.5, hours=12)
        self.assertEqual(rd2.normalized(),
            relativedelta(days=-1))

        # Equivalent to (days=-1, hours=-14, minutes=-45)
        rd3 = relativedelta(days=-1.5, hours=-2.5, minutes=-15)
        self.assertEqual(rd3.normalized(),
            relativedelta(days=-1, hours=-14, minutes=-45))

        # Equivalent to (days=-1, hours=-14, minutes=+15)
        rd4 = relativedelta(days=-1.5, hours=-2.5, minutes=45)
        self.assertEqual(rd4.normalized(),
            relativedelta(days=-1, hours=-14, minutes=+15))

        # Carry back up - equivalent to:
        # (days=-2, hours=-2, minutes=0, seconds=-2, microseconds=-3)
        rd3 = relativedelta(days=-1.5, hours=-13, minutes=-59.50045,
                            seconds=-31.473, microseconds=-500003)
        self.assertEqual(rd3.normalized(),
            relativedelta(days=-2, hours=-2, minutes=0,
                          seconds=-2, microseconds=-3))

    def testInvalidYearDay(self):
        with self.assertRaises(ValueError):
            relativedelta(yearday=367)

