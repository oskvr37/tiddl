from pathlib import Path

from tiddl.core.metadata import add_video_metadata
from tiddl.core.api.models.base import VideoQuality
from tiddl.core.utils import get_video_stream_data
from tiddl.core.utils.ffmpeg import convert_to_mp4, is_ffmpeg_installed

# we reuse Tidal API from another example
from .fetch_api import api

# Old Town Road by Lil Nas X
VIDEO_ID = 113483426
QUALITY: VideoQuality = "HIGH"

if __name__ == "__main__":
    print("fetching video_stream")
    video_stream = api.get_video_stream(video_id=VIDEO_ID, quality=QUALITY)

    # download bytes to stream_data and get the file extension
    print("downloading video_stream data")
    stream_data = get_video_stream_data(video_stream)

    filename = f"{VIDEO_ID}_{QUALITY}"

    # get file path that is located at our current directory
    video_path = Path(filename).with_suffix(".ts")

    # write data from the video_stream to our file
    print(f"saving to {video_path}")
    video_path.write_bytes(stream_data)

    if is_ffmpeg_installed():
        # convert the file from .ts to .mp4
        print("converting to mp4")
        video_path = convert_to_mp4(video_path)

        # fetch some informations about our video like title etc.
        print("getting video metadata")
        video = api.get_video(VIDEO_ID)

        # add the metadata to our saved file.
        print("saving metadata")
        add_video_metadata(video_path, video)
