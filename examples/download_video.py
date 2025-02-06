import logging

from pathlib import Path
from requests import Session

from tiddl.api import TidalApi
from tiddl.config import Config
from tiddl.download import parseVideoStream
from tiddl.utils import convertFileExtension

logging.basicConfig(level=logging.DEBUG)

VIDEO_ID = 373513584

config = Config.fromFile()  # load config from default directory

api = TidalApi(config.auth.token, config.auth.user_id, config.auth.country_code)

video_stream = api.getVideoStream(VIDEO_ID)

urls = parseVideoStream(video_stream)

with Session() as s:
    video_data = b""

    for url in urls:
        req = s.get(url)
        video_data += req.content

path = Path("videos") / f"{VIDEO_ID}.ts"
path.parent.mkdir(parents=True, exist_ok=True)

with path.open("wb") as f:
    f.write(video_data)

convertFileExtension(path, ".mp4", True, True)
