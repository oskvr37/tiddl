import requests

from pathlib import Path
from logging import getLogger

log = getLogger(__name__)


class Cover:
    uid: str
    url: str
    data: bytes | None

    def __init__(self, uid: str, size=1280) -> None:
        self.uid = uid

        if size > 1280:
            log.warning(f"can not set cover size higher than 1280 (user set: {size})")
            size = 1280

        formatted_uid = uid.replace("-", "/")

        self.url = (
            f"https://resources.tidal.com/images/{formatted_uid}/{size}x{size}.jpg"
        )

        self.data = None

    def _get_data(self) -> bytes:
        req = requests.get(self.url)

        if req.status_code != 200:
            log.error(f"could not download cover. ({req.status_code}) {self.url}")
            self.data = b""
            return b""

        log.debug(f"got cover data of {self.url}")

        self.data = req.content

        return req.content

    def save_to_directory(self, path: Path):
        file = path.with_suffix(".jpg")

        if file.exists():
            log.debug(f"cover exists ({file})")
            return

        if not self.data:
            self.data = self._get_data()

        file.parent.mkdir(parents=True, exist_ok=True)

        try:
            file.write_bytes(self.data)
        except FileNotFoundError as e:
            log.error(f"could not save cover. {file} -> {e}")
