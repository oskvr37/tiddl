import click

from utils import Context, passContext

from tiddl.types import Track


@click.group("fav")
@click.argument("type")
@passContext
def FavGroup(ctx: Context, type: str):
    """Get your Tidal favorites"""

    tracks: list[Track] = []
    ctx.obj.tracks.extend(tracks)
