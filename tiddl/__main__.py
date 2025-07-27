import click
from tiddl.ui import run_ui

@click.group()
def cli():
    """TIDDL - Tidal Downloader ♫"""
    pass

@cli.command()
def ui():
    """Launch Rich UI"""
    run_ui()

if __name__ == "__main__":
    cli()
