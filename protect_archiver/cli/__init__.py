from .download import *  # NOQA
from .events import *  # NOQA
from .sync_footage import *  # NOQA
from .sync_events import *  # NOQA


def main() -> None:
    import logging
    import os

    import urllib3

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    os.environ.setdefault("PYTHONUNBUFFERED", "true")

    # disable InsecureRequestWarning for unverified HTTPS requests
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    from .base import cli

    cli.main()
