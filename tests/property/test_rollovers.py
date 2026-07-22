"""Property tests for time handling.

Phase 0 covers the primitives the calendar modules will lean on: the virtual
timeline and silence-window membership. Phase 2 adds calendar-rollover properties
(midnight, month, intercalary month, year, BE/CE boundary) against real modules.
"""

from datetime import UTC, datetime, time

from hypothesis import given
from hypothesis import strategies as st

from coucal.config import SilenceWindow
from coucal.hal.sim.timeline import SimTimeline

_UTC = UTC


@given(
    start=st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2200, 1, 1)),
    # Integer seconds keep the check exact: two timedeltas summed vs one summed
    # can otherwise differ by a microsecond from float rounding, which is not the
    # property under test.
    a=st.integers(min_value=0, max_value=10_000_000),
    b=st.integers(min_value=0, max_value=10_000_000),
)
def test_timeline_advance_is_additive(start, a, b):
    t1 = SimTimeline(start.replace(tzinfo=_UTC))
    t1.advance(a)
    t1.advance(b)
    t2 = SimTimeline(start.replace(tzinfo=_UTC))
    t2.advance(a + b)
    assert t1.now() == t2.now()


@given(
    start=st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1)),
    secs=st.floats(min_value=0.001, max_value=1e6, allow_nan=False),
)
def test_timeline_is_monotonic(start, secs):
    t = SimTimeline(start.replace(tzinfo=_UTC))
    before = t.now()
    t.advance(secs)
    assert t.now() > before


@given(
    h1=st.integers(0, 23),
    m1=st.integers(0, 59),
    h2=st.integers(0, 23),
    m2=st.integers(0, 59),
    probe_minutes=st.integers(0, 24 * 60 - 1),
)
def test_silence_window_membership_matches_reference(h1, m1, h2, m2, probe_minutes):
    start, end = time(h1, m1), time(h2, m2)
    if start == end:
        return  # zero-length window is not a meaningful config
    w = SilenceWindow(start, end)
    probe = time(probe_minutes // 60, probe_minutes % 60)

    s = h1 * 60 + m1
    e = h2 * 60 + m2
    if s < e:
        expected = s <= probe_minutes < e
    else:  # crosses midnight
        expected = probe_minutes >= s or probe_minutes < e
    assert w.contains(probe) is expected
