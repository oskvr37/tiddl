import click

from ..ctx import Context, passContext


@click.group("fav")
@click.argument("type")
@passContext
def FavGroup(ctx: Context, type: str):
    """Get your Tidal favorites"""

    # TODO: fetch user favorites
