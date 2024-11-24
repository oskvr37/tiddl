import click

from utils import Context, passContext
from io import TextIOWrapper
from tiddl.types import Track


@click.group("file")
@click.argument("filename", type=click.File(mode="r"))
@passContext
def FileGroup(ctx: Context, filename: TextIOWrapper):
    """Parse text or JSON file with urls"""

    tracks: list[Track] = []
    ctx.obj.tracks.extend(tracks)
