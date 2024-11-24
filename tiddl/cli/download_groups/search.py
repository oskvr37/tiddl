import click

from ..utils import Context, passContext
from tiddl.types import Track


@click.group("search")
@click.argument("query")
@passContext
def SearchGroup(ctx: Context, query: str):
    """Search on Tidal"""

    tracks: list[Track] = []
    ctx.obj.tracks.extend(tracks)
