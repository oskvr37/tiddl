import subprocess
from pathlib import Path


def run(cmd: list[str]):
    """Run process without printing to terminal"""
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_ffmpeg_installed() -> bool:
    try:
        run(["ffmpeg", "-version"])
        return True
    except FileNotFoundError:
        return False


def convert_to_mp4(source: Path) -> Path:
    output_path = source.with_suffix(".mp4")

    run(["ffmpeg", "-y", "-i", str(source), "-c", "copy", str(output_path)])

    source.unlink()

    return output_path


def extract_flac(source: Path) -> Path:
    """
    Extracts flac audio from mp4 container
    """

    tmp = source.with_suffix(".tmp.flac")

    run(["ffmpeg", "-y", "-i", str(source), "-c", "copy", str(tmp)])

    tmp.replace(source.with_suffix(".flac"))

    return source.with_suffix(".flac")
