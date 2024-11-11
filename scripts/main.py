import click

from tiddl.config import Config
from tiddl.types import TrackArg


config = Config()


@click.command()
@click.argument("url", required=False)
@click.option(
    "-q",
    "--quality",
    default=config["settings"]["track_quality"],
    type=click.Choice(TrackArg.__args__, case_sensitive=False),
    help="Quality of track.",
)
@click.option(
    "-p",
    "--path",
    default=config["settings"]["download_path"],
    help="Default download path.",
)
@click.option("--save", is_flag=True, help="Save options to config.")
def cli(url: str, quality: TrackArg, path: str, save: bool):
    """
    TIDDL - Tidal Downloader.\n
    Download tracks, albums, playlists and artists.
    """

    if save:
        click.echo("Saving config")

    if url:
        click.echo(f"{url}, {quality}, {path}")


if __name__ == "__main__":
    cli()
