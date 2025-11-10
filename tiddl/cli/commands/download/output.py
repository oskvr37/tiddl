from pathlib import Path

from rich.console import Console, Group
from rich.progress import (
    Progress,
    TransferSpeedColumn,
    SpinnerColumn,
    FileSizeColumn,
    MofNCompleteColumn,
    ProgressColumn,
    BarColumn,
    Task,
    TaskID,
)
from rich.text import Text
from rich.panel import Panel


class TimeElapsedColumn(ProgressColumn):
    """Renders time elapsed."""

    def render(self, task: Task) -> Text:
        """Show time elapsed."""
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            return Text("---", style="progress.elapsed")
        return Text(f"{elapsed:.2f}s", style="progress.elapsed")


class RichOutput:
    def __init__(self, console: Console, download_height: int | None = None) -> None:
        self.console = console

        self.download_progress = Progress(
            SpinnerColumn(),
            "{task.description}",
            FileSizeColumn(),
            TransferSpeedColumn(),
            console=self.console,
        )
        self.total_progress = Progress(
            TimeElapsedColumn(),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            console=self.console,
        )

        self.group = Group(
            Panel(
                self.download_progress,
                title="Downloading",
                border_style="magenta",
                title_align="left",
                height=download_height + 2 if download_height else None,
            ),
            Panel(
                self.total_progress,
                title="Total Progress",
                border_style="green",
                title_align="left",
            ),
        )

        self.total_task = self.total_progress.add_task("Total", total=0, start=True)
        self.total_downloads = 0

    def total_increment(self, count: float = 1):
        task = self.total_progress._tasks.get(self.total_task)

        assert task is not None
        assert task.total is not None

        self.total_progress.update(self.total_task, total=task.total + count)

    def download_start(self, description: str) -> TaskID:
        return self.download_progress.add_task(description=description, total=None)

    def download_advance(self, task_id: TaskID, size: float):
        self.download_progress.update(task_id=task_id, advance=size, refresh=True)

    def download_finish(self, task_id: TaskID) -> Task:
        task = self.download_progress._tasks.get(task_id)

        assert task is not None

        self.download_progress.remove_task(task_id=task_id)
        self.total_progress.advance(self.total_task, advance=1)
        self.total_downloads += 1

        return task

    def show_stats(self):
        self.console.print(f"[green]Total downloads: {self.total_downloads}")

    def show_item_result(
        self, result_message: str, item_description: str, item_path: Path | None
    ):
        if item_path:
            description = f"[link={item_path.as_uri()}]{item_description}[/link] [link={item_path.parent.as_uri()}]{item_path.parent}[/link]"
        else:
            description = item_description

        self.console.print(f"{result_message} {description}")
