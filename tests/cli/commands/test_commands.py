import typer

from tiddl.cli.commands import register_commands, COMMANDS


def test_register_commands_adds_typers():
    app = typer.Typer()
    register_commands(app)

    registered_names = [cmd.name for cmd in app.registered_groups + app.registered_commands]

    for command in COMMANDS:
        assert command.info.name in registered_names
