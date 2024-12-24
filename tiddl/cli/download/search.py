import click

from ..ctx import Context, passContext
from tiddl.types import Track


@click.group("search")
@click.argument("query")
@passContext
def SearchGroup(ctx: Context, query: str):
    """Search on Tidal"""

    tracks: list[Track] = []

    # TODO: search on Tidal

    ctx.obj.tracks.extend(tracks)
