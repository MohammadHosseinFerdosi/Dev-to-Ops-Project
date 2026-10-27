import logging
import sys

import uvicorn

from app.config import ConfigError, Settings
from app.main import create_app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        logging.getLogger("hackathon-app").error("invalid configuration: %s", exc)
        sys.exit(1)
    uvicorn.run(create_app(settings), host="0.0.0.0", port=settings.port, access_log=True)


if __name__ == "__main__":
    main()
