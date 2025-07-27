def run_ui():
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
    from time import sleep
    import random

    console = Console()

    # Simulated Data
    downloaded_tracks = [
        {"title": "Song A", "artist": "Artist A", "quality": "MASTER", "size": "45 MB", "status": "Downloading"},
        {"title": "Song B", "artist": "Artist B", "quality": "HIGH", "size": "30 MB", "status": "Queued"},
    ]

    logs = []
    speed = 0

    def create_tracks_table():
        table = Table(title="Currently Downloaded Tracks", expand=True)
        table.add_column("Title", style="cyan")
        table.add_column("Artist", style="magenta")
        table.add_column("Quality", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Status", style="yellow")
        for track in downloaded_tracks:
            table.add_row(track["title"], track["artist"], track["quality"], track["size"], track["status"])
        return table

    def create_track_description():
        if downloaded_tracks:
            track = downloaded_tracks[0]
            desc = f"[bold]{track['title']}[/bold] by [italic]{track['artist']}[/italic]\\n"
            desc += f"Quality: {track['quality']}\\nSize: {track['size']}"
            return Panel(desc, title="Track Description")
        return Panel("No track selected", title="Track Description")

    def create_logs_panel():
        return Panel("\\n".join(logs[-5:]), title="Logs Output", border_style="blue")

    def create_speed_panel():
        return Panel(f"Current Speed: [green]{speed:.2f} MB/s[/green]", title="Download Speed", border_style="green")

    progress = Progress(
        "{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )

    total_task = progress.add_task("Total Progress", total=100)

    with Live(console=console, refresh_per_second=4) as live:
        for i in range(101):
            progress.update(total_task, completed=i)
            speed = random.uniform(1.5, 5.0)
            logs.append(f"[info] Download step {i} completed at {speed:.2f} MB/s")

            layout = Table.grid(expand=True)
            layout.add_row(create_tracks_table(), create_track_description())
            layout.add_row(progress.get_renderable())
            layout.add_row(create_logs_panel(), create_speed_panel())

            live.update(layout)
            sleep(0.1)
