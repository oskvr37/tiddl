from pathlib import Path
from logging import getLogger

from tiddl.cli.config import APP_PATH
from .models import AuthData


AUTH_DATA_FILE = APP_PATH / "auth.json"


log = getLogger(__name__)


def load_auth_data(file: Path = AUTH_DATA_FILE) -> AuthData:
    log.debug(f"loading from '{AUTH_DATA_FILE}'")

    try:
        file_content = file.read_text()
    except FileNotFoundError:
        return AuthData()

    auth_data = AuthData.model_validate_json(file_content)

    return auth_data


def save_auth_data(auth_data: AuthData, file: Path = AUTH_DATA_FILE):
    log.debug(f"saving to '{file}'")

    with file.open("w") as f:
        f.write(auth_data.model_dump_json())
