import threading
import time
from collections.abc import Callable

Clock = Callable[[], float]


class StartupGate:
    def __init__(self, delay_seconds: float, clock: Clock = time.monotonic) -> None:
        self._clock = clock
        self._ready_at = clock() + delay_seconds

    def is_started(self) -> bool:
        return self._clock() >= self._ready_at


class ReadinessGate:
    def __init__(
        self, threshold: int, cooldown_seconds: float, clock: Clock = time.monotonic
    ) -> None:
        self._threshold = threshold
        self._cooldown = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._count = 0
        self._not_ready_until: float | None = None

    @property
    def count(self) -> int:
        with self._lock:
            self._recover_if_due()
            return self._count

    def record_request(self) -> int:
        with self._lock:
            self._recover_if_due()
            self._count += 1
            if self._not_ready_until is None and self._count >= self._threshold:
                self._not_ready_until = self._clock() + self._cooldown
            return self._count

    def is_ready(self) -> bool:
        with self._lock:
            self._recover_if_due()
            return self._not_ready_until is None

    def seconds_until_ready(self) -> int:
        with self._lock:
            self._recover_if_due()
            if self._not_ready_until is None:
                return 0
            return max(0, round(self._not_ready_until - self._clock()))

    def _recover_if_due(self) -> None:
        if self._not_ready_until is not None and self._clock() >= self._not_ready_until:
            self._not_ready_until = None
            self._count = 0
