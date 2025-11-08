from os import environ
from pathlib import Path


ENV_KEY = "TIDDL_PATH"
APP_DIR_NAME = ".tiddl"


def get_app_path(env_key: str = ENV_KEY) -> Path:
    if environ.get(env_key):
        return Path(environ[env_key])

    return Path.home() / APP_DIR_NAME


def create_app_path() -> Path:
    app_path = get_app_path()
    app_path.mkdir(exist_ok=True)

    return app_path


APP_PATH = create_app_path()
