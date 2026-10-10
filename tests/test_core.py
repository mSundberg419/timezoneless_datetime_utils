import math
import unittest
from datetime import datetime, timedelta, date, time

from timezoneless_datetime_utils import NaiveDateTime, Duration
from timezoneless_datetime_utils.core import NaiveDateTime as NDT


class TestConstruction(unittest.TestCase):
    def test_basic_construction(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45, 123)
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 5)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 30)
        self.assertEqual(dt.second, 45)
        self.assertEqual(dt.microsecond, 123)

    def test_defaults_to_midnight(self):
        dt = NaiveDateTime(2023, 1, 5)
        self.assertEqual(dt.hour, 0)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)

    def test_rejects_invalid_month(self):
        with self.assertRaises(ValueError):
            NaiveDateTime(2023, 13, 1)

    def test_rejects_invalid_day(self):
        with self.assertRaises(ValueError):
            NaiveDateTime(2023, 2, 30)

    def test_rejects_feb_29_non_leap(self):
        with self.assertRaises(ValueError):
            NaiveDateTime(2023, 2, 29)

    def test_accepts_feb_29_leap(self):
        dt = NaiveDateTime(2024, 2, 29)
        self.assertEqual((dt.year, dt.month, dt.day), (2024, 2, 29))


class TestFromISO(unittest.TestCase):
    def test_round_trip_basic(self):
        dt = NaiveDateTime.from_iso("2023-01-05T12:30:45")
        self.assertEqual(dt.format(), "2023-01-05T12:30:45")

    def test_round_trip_with_microseconds(self):
        dt = NaiveDateTime.from_iso("2023-01-05T12:30:45.000123")
        self.assertEqual(dt.microsecond, 123)
        self.assertEqual(dt.format(), "2023-01-05T12:30:45.000123")

    def test_rejects_z_suffix(self):
        with self.assertRaises(ValueError):
            NaiveDateTime.from_iso("2023-01-05T12:30:45Z")

    def test_rejects_offset(self):
        with self.assertRaises(ValueError):
            NaiveDateTime.from_iso("2023-01-05T12:30:45+02:00")

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            NaiveDateTime.from_iso(12345)

    def test_whitespace_is_stripped(self):
        dt = NaiveDateTime.from_iso("  2023-01-05T12:30:45  ")
        self.assertEqual(dt.format(), "2023-01-05T12:30:45")


class TestFromDatetime(unittest.TestCase):
    def test_accepts_naive(self):
        dt = NaiveDateTime.from_datetime(datetime(2023, 1, 5, 12, 0, 0))
        self.assertEqual(dt.hour, 12)

    def test_rejects_aware(self):
        from datetime import timezone
        with self.assertRaises(ValueError):
            NaiveDateTime.from_datetime(datetime(2023, 1, 5, tzinfo=timezone.utc))


class TestFromDateAndTime(unittest.TestCase):
    def test_combines(self):
        dt = NaiveDateTime.from_date_and_time(date(2023, 1, 5), time(12, 30, 45))
        self.assertEqual(dt.format(), "2023-01-05T12:30:45")

    def test_rejects_aware_time(self):
        from datetime import timezone
        with self.assertRaises(ValueError):
            NaiveDateTime.from_date_and_time(date(2023, 1, 5),
                                             time(12, 30, 45, tzinfo=timezone.utc))


class TestArithmetic(unittest.TestCase):
    def test_add_seconds_simple(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        shifted = dt.add_seconds(90)
        self.assertEqual(shifted.format(), "2023-01-05T12:01:30")

    def test_add_seconds_rolls_into_next_day(self):
        dt = NaiveDateTime(2023, 1, 5, 23, 59, 0)
        shifted = dt.add_seconds(120)
        self.assertEqual(shifted.format(), "2023-01-06T00:01:00")

    def test_add_seconds_negative(self):
        dt = NaiveDateTime(2023, 1, 5, 0, 0, 30)
        shifted = dt.add_seconds(-30)
        self.assertEqual(shifted.format(), "2023-01-05T00:00:00")

    def test_add_seconds_crosses_month_boundary(self):
        dt = NaiveDateTime(2023, 1, 31, 23, 59, 0)
        shifted = dt.add_seconds(120)
        self.assertEqual(shifted.format(), "2023-02-01T00:01:00")

    def test_add_duration_operator(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        shifted = dt + Duration(60)
        self.assertEqual(shifted.format(), "2023-01-05T12:01:00")

    def test_sub_duration_operator(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        shifted = dt - Duration(60)
        self.assertEqual(shifted.format(), "2023-01-05T11:59:00")

    def test_sub_two_naive_returns_duration(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 30)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        diff = a - b
        self.assertIsInstance(diff, Duration)
        self.assertAlmostEqual(diff.seconds, 30.0, places=9)

    def test_sub_two_naive_negative(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 30)
        diff = a - b
        self.assertAlmostEqual(diff.seconds, -30.0, places=9)

    def test_sub_two_naive_across_days(self):
        a = NaiveDateTime(2023, 1, 6, 0, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 0, 0, 0)
        diff = a - b
        self.assertAlmostEqual(diff.seconds, 86400.0, places=6)

    def test_add_seconds_sub_microsecond_is_noop(self):
        # Documented: sub-microsecond shifts quantise to zero via timedelta.
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        shifted = dt.add_seconds(1e-7)
        self.assertEqual(shifted, dt)

    def test_add_does_not_mutate_original(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        _ = dt.add_seconds(60)
        self.assertEqual(dt.format(), "2023-01-05T12:00:00")


class TestComparisons(unittest.TestCase):
    def test_equality(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        self.assertEqual(a, b)

    def test_inequality(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 1)
        self.assertNotEqual(a, b)

    def test_ordering(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 1)
        self.assertTrue(a < b)
        self.assertTrue(a <= b)
        self.assertTrue(b > a)
        self.assertTrue(b >= a)

    def test_compare_with_naive_stdlib_datetime(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        self.assertTrue(a == datetime(2023, 1, 5, 12, 0, 0))
        self.assertTrue(a < datetime(2023, 1, 5, 12, 0, 1))

    def test_compare_with_aware_stdlib_datetime_raises(self):
        from datetime import timezone
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        with self.assertRaises(TypeError):
            _ = a < datetime(2023, 1, 5, 12, 0, 0, tzinfo=timezone.utc)

    def test_hashable(self):
        a = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        b = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)


class TestDuration(unittest.TestCase):
    def test_construction_and_seconds(self):
        d = Duration(60.0)
        self.assertAlmostEqual(d.seconds, 60.0, places=9)
        self.assertAlmostEqual(d.total_seconds, 60.0, places=9)

    def test_add_sub(self):
        a = Duration(60.0)
        b = Duration(30.0)
        self.assertAlmostEqual((a + b).seconds, 90.0, places=9)
        self.assertAlmostEqual((a - b).seconds, 30.0, places=9)

    def test_neg_and_abs(self):
        d = Duration(-60.0)
        self.assertAlmostEqual((-d).seconds, 60.0, places=9)
        self.assertAlmostEqual(abs(d).seconds, 60.0, places=9)

    def test_scalar_mul(self):
        d = Duration(60.0)
        self.assertAlmostEqual((d * 2).seconds, 120.0, places=9)
        self.assertAlmostEqual((2 * d).seconds, 120.0, places=9)

    def test_scalar_div(self):
        d = Duration(60.0)
        self.assertAlmostEqual((d / 2).seconds, 30.0, places=9)

    def test_scalar_div_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            _ = Duration(60.0) / 0

    def test_duration_div_duration(self):
        a = Duration(60.0)
        b = Duration(30.0)
        self.assertAlmostEqual(a / b, 2.0, places=9)

    def test_duration_div_by_zero_duration(self):
        with self.assertRaises(ZeroDivisionError):
            _ = Duration(60.0) / Duration(0.0)

    def test_ordering(self):
        self.assertTrue(Duration(30) < Duration(60))
        self.assertTrue(Duration(60) > Duration(30))
        self.assertTrue(Duration(60) >= Duration(60))
        self.assertTrue(Duration(60) <= Duration(60))

    def test_to_from_timedelta(self):
        d = Duration(90.0)
        td = d.to_timedelta()
        self.assertEqual(td, timedelta(seconds=90))
        back = Duration.from_timedelta(timedelta(seconds=90))
        self.assertAlmostEqual(back.seconds, 90.0, places=9)

    def test_equality_and_hash(self):
        a = Duration(60.0)
        b = Duration(60.0)
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_float_seconds_preserved(self):
        d = Duration(60.25)
        self.assertAlmostEqual(d.seconds, 60.25, places=9)

    def test_repr(self):
        self.assertIn("Duration", repr(Duration(5.0)))


class TestFormat(unittest.TestCase):
    def test_default_sep(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45)
        self.assertEqual(dt.format(), "2023-01-05T12:30:45")

    def test_custom_sep(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45)
        self.assertEqual(dt.format(sep=" "), "2023-01-05 12:30:45")

    def test_microseconds_included_when_nonzero(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45, 123)
        self.assertEqual(dt.format(), "2023-01-05T12:30:45.000123")

    def test_microseconds_omitted_when_zero(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45, 0)
        self.assertEqual(dt.format(), "2023-01-05T12:30:45")

    def test_str_and_repr(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45)
        self.assertEqual(str(dt), "2023-01-05T12:30:45")
        self.assertIn("NaiveDateTime", repr(dt))

    def test_format_rejects_non_str_sep(self):
        dt = NaiveDateTime(2023, 1, 5)
        with self.assertRaises(TypeError):
            dt.format(sep=123)


class TestReplace(unittest.TestCase):
    def test_replace_hour(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        r = dt.replace(hour=14)
        self.assertEqual(r.hour, 14)
        self.assertEqual(dt.hour, 12)  # original unchanged

    def test_replace_multiple(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 0, 0)
        r = dt.replace(month=2, day=10, minute=30)
        self.assertEqual(r.format(), "2023-02-10T12:30:00")


class TestAccessors(unittest.TestCase):
    def test_date_and_time(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45, 123)
        self.assertEqual(dt.date, date(2023, 1, 5))
        self.assertEqual(dt.time, time(12, 30, 45, 123))

    def test_to_datetime_round_trip(self):
        dt = NaiveDateTime(2023, 1, 5, 12, 30, 45)
        back = NaiveDateTime.from_datetime(dt.to_datetime())
        self.assertEqual(dt, back)


class TestReexports(unittest.TestCase):
    def test_names_match(self):
        from timezoneless_datetime_utils import NaiveDateTime as A, Duration as B
        from timezoneless_datetime_utils.core import NaiveDateTime as A2, Duration as B2
        self.assertIs(A, A2)
        self.assertIs(B, B2)


if __name__ == "__main__":
    unittest.main()
