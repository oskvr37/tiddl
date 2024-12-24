import click

from ..ctx import Context, passContext

from tiddl.types import Track


@click.group("fav")
@click.argument("type")
@passContext
def FavGroup(ctx: Context, type: str):
    """Get your Tidal favorites"""

    tracks: list[Track] = []

    # TODO: fetch user favorites

    ctx.obj.tracks.extend(tracks)
