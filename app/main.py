import logging
import socket
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.central import CentralClient, HttpCentralClient
from app.config import Settings
from app.lifecycle import Clock, ReadinessGate, StartupGate

log = logging.getLogger("hackathon-app")


def create_app(
    settings: Settings | None = None,
    clock: Clock = time.monotonic,
    central: CentralClient | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    central = central or HttpCentralClient()
    startup = StartupGate(settings.startup_delay_seconds, clock)
    readiness = ReadinessGate(settings.request_threshold, settings.not_ready_seconds, clock)
    hostname = socket.gethostname()

    app = FastAPI(title="Platform hackathon app", docs_url=None, redoc_url=None)

    log.info(
        "config loaded: REQUEST_THRESHOLD=%s NOT_READY_SECONDS=%s STARTUP_DELAY_SECONDS=%s "
        "PARTICIPANT=%s APP_SECRET=%s CENTRAL_SERVICE_URL=%s",
        settings.request_threshold,
        settings.not_ready_seconds,
        settings.startup_delay_seconds,
        settings.participant,
        "set" if settings.app_secret else "empty",
        settings.central_service_url or "empty",
    )

    def starting() -> JSONResponse:
        return JSONResponse({"status": "starting"}, status_code=503)

    @app.get("/live")
    def live():
        if not startup.is_started():
            return starting()
        return {"status": "alive"}

    @app.get("/ready")
    def ready():
        if not startup.is_started():
            return starting()
        if not readiness.is_ready():
            return JSONResponse(
                {"status": "not ready", "retry_after_seconds": readiness.seconds_until_ready()},
                status_code=503,
            )
        return {"status": "ready"}

    @app.get("/hello")
    def hello():
        if not startup.is_started():
            return starting()
        count = readiness.record_request()
        if count == settings.request_threshold:
            log.warning(
                "request threshold reached (%s): /ready returns 503 for %ss",
                count,
                settings.not_ready_seconds,
            )
        return {
            "message": settings.greeting,
            "participant": settings.participant,
            "hostname": hostname,
            "request_count": count,
            "request_threshold": settings.request_threshold,
            "secret_loaded": bool(settings.app_secret),
            "secret_fingerprint": settings.secret_fingerprint,
        }

    @app.get("/central")
    def call_central():
        if not settings.central_service_url:
            return JSONResponse({"error": "CENTRAL_SERVICE_URL is not set"}, status_code=500)
        status, body = central.check_in(settings.central_service_url, settings.participant)
        if status == 0:
            return JSONResponse({"error": f"central service unreachable: {body}"}, status_code=502)
        return {"central_status": status, "central_response": body}

    return app
