# timezoneless_datetime_utils

A small, focused library for representing and manipulating datetimes that carry **no** timezone or UTC-offset information. It wraps the standard-library `datetime`, adds a `Duration` rooted in seconds, and refuses to accept timezone-aware values anywhere on the boundary.

## Why

Naive and timezone-aware `datetime` objects mix silently in Python until something breaks at a comparison or an arithmetic step — and the failure is rarely near the cause. This library makes naiveness an enforced property of the type: every constructor and parser rejects aware values, so a conversion has to happen explicitly at the edge of your system rather than by accident in the middle.

The trade-off is that this library will not help you convert between zones. If your data has offsets, strip them yourself first — intentionally — and then work in naive space.

## Usage

```python
from timezoneless_datetime_utils import NaiveDateTime, Duration

dt = NaiveDateTime(2023, 1, 5, 12, 30, 45)
shifted = dt + Duration(90)          # 2023-01-05T12:31:30
parsed = NaiveDateTime.from_iso("2023-01-05T12:30:45")

# Differences between two naive datetimes are returned as a Duration:
lag = NaiveDateTime(2023, 1, 5, 12, 30, 45) - NaiveDateTime(2023, 1, 5, 12, 0, 0)
print(lag.seconds)  # 1845.0

# Rejected at the boundary:
# NaiveDateTime.from_iso("2023-01-05T12:30:45Z")  # raises ValueError
```

## Exported names

- `NaiveDateTime` — the naive datetime type. Construct as `NaiveDateTime(year, month, day, hour=0, minute=0, second=0, microsecond=0)`, or via `from_iso`, `from_datetime`, `from_date_and_time`.
- `Duration` — a real-valued length of time in seconds. Supports `+`, `-`, `*` (scalar), `/` (scalar or Duration), ordering, hashing, and `to_timedelta` / `from_timedelta`.

## Awkward edges

- **Sub-microsecond shifts are no-ops.** `add_seconds(1e-7)` quantises to zero microseconds through `timedelta` and returns an equal datetime. This is documented rather than silently approximated.
- **`Duration` seconds are floats.** Comparisons in the test suite use `assertAlmostEqual` with tight tolerances; do not use `==` on `Duration` in your own code unless you constructed both from exact integers.
- **`from_iso` rejects anything that looks timezone-aware** — a trailing `Z`, a `+HH:MM` or `-HH:MM` after the 10th character — even though `datetime.fromisoformat` would accept some of them. Pass a strictly naive `YYYY-MM-DDTHH:MM:SS[.ffffff]` string.
- **Comparing a `NaiveDateTime` with a tz-aware stdlib `datetime` raises `TypeError`** rather than falling back to identity comparison.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

No third-party dependencies. Standard library only.
