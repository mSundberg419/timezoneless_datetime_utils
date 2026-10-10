# timezoneless_datetime_utils/core.py

from __future__ import annotations

from datetime import datetime, timedelta, date as _date, time as _time

__all__ = ["NaiveDateTime", "Duration"]


class Duration:
    """An amount of time expressed in real-valued seconds.

    The standard library's timedelta is built around integer days/seconds with
    microsecond resolution and forces callers to reason about its internal
    decomposition. This library's arithmetic is rooted in seconds — the unit
    users actually pass in — and preserves whatever fractional precision
    Python floats provide. We avoid exact equality tests on Duration values
    throughout the test suite precisely because floating-point seconds are
    inexact by design; comparisons use abs(a-b) < epsilon instead.
    """

    __slots__ = ("_seconds",)

    def __init__(self, seconds: float) -> None:
        self._seconds = float(seconds)

    @property
    def seconds(self) -> float:
        return self._seconds

    @property
    def total_seconds(self) -> float:
        """Alias for seconds so the name parallels timedelta.total_seconds()."""
        return self._seconds

    def __add__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(self._seconds + other._seconds)

    def __sub__(self, other: "Duration") -> "Duration":
        if not isinstance(other, Duration):
            return NotImplemented
        return Duration(self._seconds - other._seconds)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds == other._seconds

    def __hash__(self) -> int:
        return hash(self._seconds)

    def __lt__(self, other: "Duration") -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds < other._seconds

    def __le__(self, other: "Duration") -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds <= other._seconds

    def __gt__(self, other: "Duration") -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds > other._seconds

    def __ge__(self, other: "Duration") -> bool:
        if not isinstance(other, Duration):
            return NotImplemented
        return self._seconds >= other._seconds

    def __neg__(self) -> "Duration":
        return Duration(-self._seconds)

    def __abs__(self) -> "Duration":
        return Duration(abs(self._seconds))

    def __mul__(self, factor: float) -> "Duration":
        if not isinstance(factor, (int, float)):
            return NotImplemented
        return Duration(self._seconds * float(factor))

    __rmul__ = __mul__

    def __truediv__(self, divisor):
        if isinstance(divisor, Duration):
            if divisor._seconds == 0.0:
                raise ZeroDivisionError("cannot divide by a zero-length Duration")
            return self._seconds / divisor._seconds
        if not isinstance(divisor, (int, float)):
            return NotImplemented
        d = float(divisor)
        if d == 0.0:
            raise ZeroDivisionError("cannot divide a Duration by zero")
        return Duration(self._seconds / d)

    def __repr__(self) -> str:
        return f"Duration(seconds={self._seconds!r})"

    def to_timedelta(self) -> timedelta:
        """Convert to a standard-library timedelta.

        This is the bridge to the rest of the datetime ecosystem. Because
        timedelta stores microseconds as integers, fractional seconds beyond
        microsecond precision are truncated — an inherent limitation of the
        target type, not a bug here.
        """
        return timedelta(seconds=self._seconds)

    @classmethod
    def from_timedelta(cls, td: timedelta) -> "Duration":
        return cls(td.total_seconds())


class NaiveDateTime:
    """A datetime that carries no timezone or offset.

    This class deliberately wraps the stdlib datetime but never accepts or
    produces tz-aware values. The rationale: mixing naive and aware datetimes
    is a frequent source of silent bugs in Python. By making naiveness an
    explicit, enforced property of the type we force callers to convert at
    the boundary instead of hoping arithmetic will do the right thing.
    """

    __slots__ = ("_dt",)

    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0):
        # We construct a datetime directly so that the stdlib's own validation
        # for ranges (leap seconds rejected, month in 1..12, etc.) applies.
        dt = datetime(year, month, day, hour, minute, second, microsecond)
        if dt.tzinfo is not None:  # belt-and-braces; datetime() with no tzinfo won't set it
            raise ValueError("NaiveDateTime must not have timezone info")
        self._dt = dt

    # ----- constructors -----

    @classmethod
    def from_datetime(cls, dt: datetime) -> "NaiveDateTime":
        """Promote a stdlib datetime; reject tz-aware values.

        Accepting aware datetimes here would defeat the point of this class.
        Callers who need to drop a timezone must call .replace(tzinfo=None)
        themselves so the intent is explicit at the call site.
        """
        if dt.tzinfo is not None:
            raise ValueError(
                "from_datetime refuses tz-aware values; "
                "call .replace(tzinfo=None) explicitly first"
            )
        inst = cls.__new__(cls)
        inst._dt = dt.replace(tzinfo=None)
        return inst

    @classmethod
    def from_iso(cls, s: str) -> "NaiveDateTime":
        """Parse a restricted subset of ISO 8601: YYYY-MM-DDTHH:MM:SS[.ffffff].

        We deliberately reject any string containing an offset ('Z', '+HH:MM',
        '-HH:MM') so that a value that LOOKS naive but secretly carries
        timezone intent is not silently swallowed. Python 3.11+'s
        datetime.fromisoformat accepts offsets; we post-filter to keep
        behaviour identical on 3.7+.
        """
        if not isinstance(s, str):
            raise TypeError("from_iso expects a str")
        stripped = s.strip()
        upper = stripped.upper()
        if upper.endswith("Z") or "+" in stripped[10:] or "-" in stripped[10:]:
            raise ValueError(
                "from_iso rejects timezone-aware strings; "
                "pass a naive YYYY-MM-DDTHH:MM:SS form"
            )
        # datetime.fromisoformat on 3.7+ handles the core subset we allow.
        dt = datetime.fromisoformat(stripped)
        if dt.tzinfo is not None:
            raise ValueError("parsed datetime unexpectedly carried tzinfo")
        return cls.from_datetime(dt)

    @classmethod
    def from_date_and_time(cls, d: _date, t: _time) -> "NaiveDateTime":
        if t.tzinfo is not None:
            raise ValueError("time component must be naive")
        return cls(d.year, d.month, d.day, t.hour, t.minute, t.second, t.microsecond)

    # ----- accessors -----

    @property
    def year(self) -> int: return self._dt.year
    @property
    def month(self) -> int: return self._dt.month
    @property
    def day(self) -> int: return self._dt.day
    @property
    def hour(self) -> int: return self._dt.hour
    @property
    def minute(self) -> int: return self._dt.minute
    @property
    def second(self) -> int: return self._dt.second
    @property
    def microsecond(self) -> int: return self._dt.microsecond

    @property
    def date(self) -> _date:
        return self._dt.date()

    @property
    def time(self) -> _time:
        return self._dt.time()

    def to_datetime(self) -> datetime:
        """Return a naive stdlib datetime (tzinfo is None by construction)."""
        return self._dt

    # ----- arithmetic -----

    def add_seconds(self, seconds: float) -> "NaiveDateTime":
        """Return a new NaiveDateTime shifted by a real-valued number of seconds.

        We go through timedelta, which quantises to microseconds. Sub-microsecond
        shifts are therefore no-ops — documented rather than silently approximated.
        """
        return self.add_duration(Duration(seconds))

    def add_duration(self, duration: Duration) -> "NaiveDateTime":
        if not isinstance(duration, Duration):
            raise TypeError("add_duration expects a Duration")
        new = self._dt + duration.to_timedelta()
        # timedelta + naive datetime stays naive; assert to be safe.
        if new.tzinfo is not None:
            raise AssertionError("internal: arithmetic produced tz-aware value")
        inst = NaiveDateTime.__new__(NaiveDateTime)
        inst._dt = new
        return inst

    def __add__(self, other):
        if isinstance(other, Duration):
            return self.add_duration(other)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Duration):
            return self.add_duration(-other)
        if isinstance(other, NaiveDateTime):
            return Duration((self._dt - other._dt).total_seconds())
        return NotImplemented

    # ----- comparisons -----

    def _coerce(self, other):
        if isinstance(other, NaiveDateTime):
            return other._dt
        if isinstance(other, datetime):
            if other.tzinfo is not None:
                raise TypeError("cannot compare NaiveDateTime with tz-aware datetime")
            return other
        return None

    def __eq__(self, other: object) -> bool:
        o = self._coerce(other)
        if o is None:
            return NotImplemented
        return self._dt == o

    def __lt__(self, other) -> bool:
        o = self._coerce(other)
        if o is None:
            return NotImplemented
        return self._dt < o

    def __le__(self, other) -> bool:
        o = self._coerce(other)
        if o is None:
            return NotImplemented
        return self._dt <= o

    def __gt__(self, other) -> bool:
        o = self._coerce(other)
        if o is None:
            return NotImplemented
        return self._dt > o

    def __ge__(self, other) -> bool:
        o = self._coerce(other)
        if o is None:
            return NotImplemented
        return self._dt >= o

    def __hash__(self) -> int:
        return hash(self._dt)

    # ----- formatting -----

    def format(self, sep: str = "T") -> str:
        """Format as YYYY-MM-DD<sep>HH:MM:SS[.ffffff].

        Microseconds are omitted when zero so that whole-second values stay
        round-trippable through from_iso without noise.
        """
        if not isinstance(sep, str):
            raise TypeError("sep must be a str")
        base = self._dt.strftime("%Y-%m-%d") + sep + self._dt.strftime("%H:%M:%S")
        if self._dt.microsecond:
            base += ".{:06d}".format(self._dt.microsecond)
        return base

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return f"NaiveDateTime('{self.format()}')"

    def replace(self, *, year=None, month=None, day=None, hour=None, minute=None,
                second=None, microsecond=None) -> "NaiveDateTime":
        """Return a copy with selected fields replaced.

        Mirrors datetime.replace but always produces a naive value. We do NOT
        accept a tzinfo keyword — passing one would be a caller bug.
        """
        new = self._dt.replace(
            year=year if year is not None else self._dt.year,
            month=month if month is not None else self._dt.month,
            day=day if day is not None else self._dt.day,
            hour=hour if hour is not None else self._dt.hour,
            minute=minute if minute is not None else self._dt.minute,
            second=second if second is not None else self._dt.second,
            microsecond=microsecond if microsecond is not None else self._dt.microsecond,
        )
        return NaiveDateTime.from_datetime(new)
