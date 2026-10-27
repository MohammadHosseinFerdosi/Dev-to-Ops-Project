import json
import socket
import urllib.error
import urllib.request
from typing import Protocol


class CentralClient(Protocol):
    def check_in(self, url: str, participant: str) -> tuple[int, str]: ...


class HttpCentralClient:
    def __init__(self, timeout_seconds: float = 3.0) -> None:
        self._timeout = timeout_seconds

    def check_in(self, url: str, participant: str) -> tuple[int, str]:
        payload = json.dumps({"participant": participant, "hostname": socket.gethostname()})
        request = urllib.request.Request(
            url,
            data=payload.encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                return response.status, response.read(2048).decode(errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(2048).decode(errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            return 0, str(reason)
