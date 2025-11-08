from pathlib import Path

from tiddl.core.utils import get_track_stream_data
from tiddl.core.metadata import add_track_metadata
from tiddl.core.api.models import TrackQuality

# we reuse Tidal API from another example
from .fetch_api import api

# Congratulations by Post Malone
TRACK_ID = 77662595
QUALITY: TrackQuality = "LOSSLESS"

if __name__ == "__main__":
    # fetch track_stream
    track_stream = api.get_track_stream(TRACK_ID, QUALITY)

    # download bytes to stream_data and get the file extension
    stream_data, file_extension = get_track_stream_data(track_stream)

    filename = f"{TRACK_ID}_{track_stream.audioQuality}"

    # get file path that is located at our current directory
    # with filename: TRACK_ID_QUALITY.EXTENSION
    track_path = Path(filename).with_suffix(file_extension)

    # write data from the track_stream to our file
    track_path.write_bytes(stream_data)

    # fetch some informations about our track like title etc.
    track = api.get_track(TRACK_ID)

    # add the metadata to our saved file.
    # note that not every data is added such as cover or lyrics.
    add_track_metadata(track_path, track)

    # Congratulations if it works on your machine
