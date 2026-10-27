import pytest

from app.lifecycle import ReadinessGate, StartupGate


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def test_startup_gate_is_not_started_before_delay(clock):
    gate = StartupGate(delay_seconds=15, clock=clock)
    clock.advance(14.9)
    assert gate.is_started() is False


def test_startup_gate_is_started_after_delay(clock):
    gate = StartupGate(delay_seconds=15, clock=clock)
    clock.advance(15)
    assert gate.is_started() is True


def test_startup_gate_with_zero_delay_starts_immediately(clock):
    assert StartupGate(delay_seconds=0, clock=clock).is_started() is True


def test_readiness_gate_stays_ready_below_threshold(clock):
    gate = ReadinessGate(threshold=10, cooldown_seconds=30, clock=clock)
    for _ in range(9):
        gate.record_request()
    assert gate.is_ready() is True


def test_readiness_gate_becomes_not_ready_at_threshold(clock):
    gate = ReadinessGate(threshold=10, cooldown_seconds=30, clock=clock)
    for _ in range(10):
        gate.record_request()
    assert gate.is_ready() is False
    assert gate.seconds_until_ready() == 30


def test_readiness_gate_recovers_after_cooldown(clock):
    gate = ReadinessGate(threshold=10, cooldown_seconds=30, clock=clock)
    for _ in range(10):
        gate.record_request()
    clock.advance(30)
    assert gate.is_ready() is True
    assert gate.count == 0


def test_requests_during_cooldown_do_not_extend_it(clock):
    gate = ReadinessGate(threshold=10, cooldown_seconds=30, clock=clock)
    for _ in range(10):
        gate.record_request()
    clock.advance(20)
    for _ in range(5):
        gate.record_request()
    clock.advance(10)
    assert gate.is_ready() is True
    assert gate.count == 0


def test_record_request_returns_running_count(clock):
    gate = ReadinessGate(threshold=10, cooldown_seconds=30, clock=clock)
    assert gate.record_request() == 1
    assert gate.record_request() == 2
