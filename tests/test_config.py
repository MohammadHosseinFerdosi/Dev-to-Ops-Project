import pytest

from app.config import ConfigError, Settings


def test_defaults_when_env_is_empty():
    s = Settings.from_env({})
    assert s.request_threshold == 10
    assert s.not_ready_seconds == 30
    assert s.startup_delay_seconds == 40
    assert s.greeting == "Hello from Platform"
    assert s.app_secret == ""
    assert s.central_service_url == ""
    assert s.port == 8080


def test_port_is_read_from_env():
    assert Settings.from_env({"PORT": "9000"}).port == 9000


def test_values_are_read_from_env():
    s = Settings.from_env(
        {
            "REQUEST_THRESHOLD": "3",
            "NOT_READY_SECONDS": "5",
            "STARTUP_DELAY_SECONDS": "0",
            "GREETING": "Salam",
            "APP_SECRET": "s3cr3t",
            "PARTICIPANT": "a.haririan",
            "CENTRAL_SERVICE_URL": "http://central.hackathon.svc:8080/checkin",
        }
    )
    assert (s.request_threshold, s.not_ready_seconds, s.startup_delay_seconds) == (3, 5, 0)
    assert s.greeting == "Salam"
    assert s.app_secret == "s3cr3t"
    assert s.participant == "a.haririan"
    assert s.central_service_url == "http://central.hackathon.svc:8080/checkin"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("REQUEST_THRESHOLD", "abc"),
        ("REQUEST_THRESHOLD", "0"),
        ("NOT_READY_SECONDS", "-1"),
        ("STARTUP_DELAY_SECONDS", "1.5"),
        ("PORT", "0"),
    ],
)
def test_invalid_numbers_are_rejected_with_variable_name(name, value):
    with pytest.raises(ConfigError, match=name):
        Settings.from_env({name: value})


def test_secret_fingerprint_hides_value():
    s = Settings.from_env({"APP_SECRET": "s3cr3t"})
    assert "s3cr3t" not in s.secret_fingerprint
    assert len(s.secret_fingerprint) == 8


def test_secret_fingerprint_is_empty_without_secret():
    assert Settings.from_env({}).secret_fingerprint == ""
