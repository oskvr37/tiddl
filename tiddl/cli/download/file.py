import click
import json

from io import TextIOWrapper
from os.path import splitext

from ..ctx import Context, passContext
from tiddl.utils import TidalResource


@click.group("file")
@click.argument("filename", type=click.File(mode="r"))
@passContext
def FileGroup(ctx: Context, filename: TextIOWrapper):
    """Parse txt or JSON file with urls"""

    _, extension = splitext(filename.name)

    resource_strings: list[str]

    match extension:
        case ".json":
            try:
                resource_strings = json.load(filename)
            except json.JSONDecodeError as e:
                raise click.UsageError(f"Cant decode JSON file - {e.msg}")

        case ".txt":
            resource_strings = [line.strip() for line in filename.readlines()]

        case _:
            raise click.UsageError(f"Unsupported file extension - {extension}")

    for string in resource_strings:
        try:
            ctx.obj.resources.append(TidalResource(string))
        except ValueError as e:
            click.echo(click.style(e, "red"))

    click.echo(click.style(f"Loaded {len(ctx.obj.resources)} resources", "green"))
