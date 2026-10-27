import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeCentral:
    def __init__(self, status: int = 200, body: str = "registered") -> None:
        self.status = status
        self.body = body
        self.calls: list[tuple[str, str]] = []

    def check_in(self, url: str, participant: str) -> tuple[int, str]:
        self.calls.append((url, participant))
        return self.status, self.body


def make_client(clock, central=None, **env):
    base = {"REQUEST_THRESHOLD": "3", "NOT_READY_SECONDS": "30", "STARTUP_DELAY_SECONDS": "0"}
    base.update(env)
    app = create_app(Settings.from_env(base), clock=clock, central=central or FakeCentral())
    return TestClient(app)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def test_hello_returns_greeting_and_count(clock):
    client = make_client(clock, GREETING="Salam")
    body = client.get("/hello").json()
    assert body["message"] == "Salam"
    assert body["request_count"] == 1
    assert body["request_threshold"] == 3
    assert "hostname" in body


def test_hello_shows_secret_fingerprint_not_value(clock):
    client = make_client(clock, APP_SECRET="s3cr3t")
    body = client.get("/hello").json()
    assert body["secret_loaded"] is True
    assert "s3cr3t" not in str(body)


def test_live_and_ready_are_ok_after_start(clock):
    client = make_client(clock)
    assert client.get("/live").status_code == 200
    assert client.get("/ready").status_code == 200


def test_probes_do_not_increment_request_count(clock):
    client = make_client(clock)
    for _ in range(5):
        client.get("/live")
        client.get("/ready")
    assert client.get("/hello").json()["request_count"] == 1


def test_ready_returns_503_after_threshold_while_live_stays_200(clock):
    client = make_client(clock)
    for _ in range(3):
        client.get("/hello")
    ready = client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["retry_after_seconds"] == 30
    assert client.get("/live").status_code == 200


def test_ready_recovers_after_cooldown(clock):
    client = make_client(clock)
    for _ in range(3):
        client.get("/hello")
    clock.advance(30)
    assert client.get("/ready").status_code == 200
    assert client.get("/hello").json()["request_count"] == 1


def test_all_endpoints_return_503_during_startup(clock):
    client = make_client(clock, STARTUP_DELAY_SECONDS="40")
    for path in ("/live", "/ready", "/hello"):
        assert client.get(path).status_code == 503, path
    clock.advance(40)
    for path in ("/live", "/ready", "/hello"):
        assert client.get(path).status_code == 200, path


def test_hello_during_startup_is_not_counted(clock):
    client = make_client(clock, STARTUP_DELAY_SECONDS="10")
    client.get("/hello")
    clock.advance(10)
    assert client.get("/hello").json()["request_count"] == 1


def test_central_without_url_explains_missing_config(clock):
    client = make_client(clock)
    r = client.get("/central")
    assert r.status_code == 500
    assert "CENTRAL_SERVICE_URL" in r.json()["error"]


def test_central_checks_in_with_participant(clock):
    central = FakeCentral(status=200, body="welcome")
    client = make_client(
        clock, central=central, CENTRAL_SERVICE_URL="http://central/checkin", PARTICIPANT="ali"
    )
    r = client.get("/central")
    assert r.status_code == 200
    assert r.json() == {"central_status": 200, "central_response": "welcome"}
    assert central.calls == [("http://central/checkin", "ali")]


def test_central_unreachable_returns_502(clock):
    central = FakeCentral(status=0, body="connection refused")
    client = make_client(clock, central=central, CENTRAL_SERVICE_URL="http://central/checkin")
    r = client.get("/central")
    assert r.status_code == 502
    assert "connection refused" in r.json()["error"]
