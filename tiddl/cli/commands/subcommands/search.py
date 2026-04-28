import typer
from typing_extensions import Annotated

from tiddl.cli.ctx import Context
from tiddl.cli.utils.resource import TidalResource
from tiddl.core.api.models.base import Search, SearchArtist
from tiddl.core.api.models.resources import Track, Album, Playlist

from rich.panel import Panel
from rich.table import Table


search_subcommand = typer.Typer()

@search_subcommand.command(
    no_args_is_help=True,
)



def search(
    ctx: Context,
    query: Annotated[str, typer.Argument()],
    resource_types: Annotated[
        list[str],
        typer.Option(
            "-t",
            "--types",
            metavar="<resource>",
            help="Narrow resource types, usage: -t track -t album etc. Available resources: track, video, album, playlist, artist.",
        ),
    ] = ["track", "video", "album", "playlist", "artist"],    top_per_type: Annotated[int, typer.Option("--num-top", "-n", help="Number of top results to display per resource type.")] = 3,
    pick_top_hit: Annotated[bool, typer.Option("--top", "-T", help="Automatically pick the top hit if it exists and matches the specified resource types.")] = False,
):
    """
    Search Tidal for tracks, videos, albums, playlists, artists, and mixes.

    By default, it searches for all resource types. You can specify which resource types to search for using the `--type` option.
    """
    results: Search = ctx.obj.api.get_search(query=query)
    table = _prepare_table(query)
    
    results_to_display = []
    if results.topHit is not None:
        top_hit = results.topHit
        top_hit_type = top_hit.type.rstrip("S").lower()  # "ARTISTS" -> "artist"
        if top_hit_type in resource_types:
            if pick_top_hit:
                ctx.obj.resources.append(TidalResource.from_string(f"{top_hit_type}/{_display_id(top_hit.value)}"))
                ctx.obj.console.print(f"[green]Automatically added top hit: {top_hit.type.title()} '{_display_name(top_hit.value)}'")
                return
            else:
                results_to_display.append(
                    (top_hit_type.title(), _display_name(top_hit.value), _display_id(top_hit.value))
                )
    
    type_to_items = {
        "artist":   results.artists.items,
        "album":    results.albums.items,
        "playlist": results.playlists.items,
        "track":    results.tracks.items,
        "video":    results.videos.items,
    }

    for resource_type, items in type_to_items.items():
        if resource_type in resource_types:
            results_to_display.extend(
                (resource_type.title(), _display_name(item), _display_id(item))
                for item in items[:top_per_type]
            )
    
    for i, (resource_type, name, id) in enumerate(results_to_display, start=1):
        table.add_row(str(i), resource_type, name, id)
    panel = Panel(table, title="Search Results", highlight=True, expand=True)
    ctx.obj.console.print(panel)
    selection = ctx.obj.console.input("[bold green]Enter the number of the resource to add to your list (comma-separated for multiple, q/empty = quit): ")
    selected_numbers = [s.strip() for s in selection.split(",")]
    for num in selected_numbers:
        if num.lower() == "q":
            return
        if not num.isdigit() or int(num) < 1 or int(num) > len(results_to_display):
            ctx.obj.console.print(f"[red]Invalid selection: {num}")
            continue
        selected_resource = results_to_display[int(num)-1]
        resource_type, name, id = selected_resource
        ctx.obj.resources.append(TidalResource.from_string(f"{resource_type.lower()}/{id}"))
        ctx.obj.console.print(f"[green]Added {resource_type} '{name}' to your list")


def _display_name(item) -> str:
    # if searchArtist, else if track/album, else playlist
    if isinstance(item, SearchArtist):
        return item.name
    elif isinstance(item, (Track, Album)):
        # Try to format as "Main Artist - Title" 
        main_artist = item.artists[0] if item.artists else None
        return f"{main_artist.name} - {item.title}" if main_artist else f"{item.title}"
    else:  # Playlist
        return item.title

def _display_id(item) -> str:
    return item.uuid if isinstance(item, Playlist) else str(item.id)
        
def _prepare_table(query: str) -> Table:
    table = Table(title=f"{query}", expand=True)
    table.add_column("#", style="yellow", ratio=1)
    table.add_column("Type", style="cyan", ratio=1)
    table.add_column("Title", style="green", ratio=8)
    table.add_column("ID", style="magenta", ratio=2)
    return table