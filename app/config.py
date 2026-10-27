import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(ValueError):
    pass


def _int(env: Mapping[str, str], name: str, default: int, minimum: int) -> int:
    raw = env.get(name, "").strip()
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    request_threshold: int
    not_ready_seconds: int
    startup_delay_seconds: int
    greeting: str
    app_secret: str
    participant: str
    central_service_url: str
    port: int

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        return cls(
            request_threshold=_int(env, "REQUEST_THRESHOLD", 10, 1),
            not_ready_seconds=_int(env, "NOT_READY_SECONDS", 30, 0),
            startup_delay_seconds=_int(env, "STARTUP_DELAY_SECONDS", 40, 0),
            greeting=env.get("GREETING", "") or "Hello from Platform",
            app_secret=env.get("APP_SECRET", ""),
            participant=env.get("PARTICIPANT", "") or "anonymous",
            central_service_url=env.get("CENTRAL_SERVICE_URL", ""),
            port=_int(env, "PORT", 8080, 1),
        )

    @property
    def secret_fingerprint(self) -> str:
        if not self.app_secret:
            return ""
        return hashlib.sha256(self.app_secret.encode()).hexdigest()[:8]
