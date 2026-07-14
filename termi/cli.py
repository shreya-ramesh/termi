from __future__ import annotations

import sys

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table

from termi.core.agent import Agent, CommandProposal
from termi.core.conversation import ConversationManager
from termi.core.provider_manager import ProviderManager
from termi.core.settings import SettingsManager
from termi.core.system_query import SystemInfoSnapshot, detect_system_info_query
from termi.database.database import Database
from termi.providers.factory import DEFAULT_MODELS, SUPPORTED_PROVIDERS
from termi.utils.exceptions import TermiError
from termi.utils.logger import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    name="termi",
    help="AI-powered cross-platform terminal assistant.",
    add_completion=True,
    no_args_is_help=False,
)

SLASH_COMMANDS = (
    "/provider",
    "/provider list",
    "/provider set <name>",
    "/os",
    "/shell",
    "/history",
    "/history clear",
    "/settings",
    "/settings show",
    "/settings edit",
    "/help",
    "/exit",
    "/retry",
    "/explain <command>",
)


class TermiSession:

    def __init__(self) -> None:
        load_dotenv()
        self.settings_manager = SettingsManager()
        settings = self.settings_manager.settings
        self.database = Database()
        self.provider_manager = ProviderManager(settings.provider, settings.model)
        self.conversation = ConversationManager(history_size=settings.history_size)
        self.agent = Agent(
            settings_manager=self.settings_manager,
            provider_manager=self.provider_manager,
            database=self.database,
            conversation_manager=self.conversation,
        )


def _print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Termi[/bold cyan] — AI-powered terminal assistant\n"
            "Type a request in plain English, or [bold]/help[/bold] for commands.",
            border_style="cyan",
        )
    )


def _print_help() -> None:
    table = Table(title="Termi Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command")
    table.add_column("Description")
    table.add_row("/provider", "Show the active provider")
    table.add_row("/provider list", "List all supported providers")
    table.add_row("/provider set <name>", "Switch the active provider")
    table.add_row("/os", "Show the detected operating system")
    table.add_row("/shell", "Show the detected shell")
    table.add_row("/history", "Show recent command history")
    table.add_row("/history clear", "Delete all stored history")
    table.add_row("/settings", "Show current settings")
    table.add_row("/settings show", "Show current settings")
    table.add_row("/settings edit <key> <value>", "Update a setting")
    table.add_row("/explain <command>", "Explain what a shell command does")
    table.add_row("/retry", "Regenerate a command for the last prompt")
    table.add_row("/help", "Show this help message")
    table.add_row("/exit", "Exit Termi")
    console.print(table)


def _render_proposal(proposal: CommandProposal) -> None:
    syntax = Syntax(proposal.command, "bash", theme="monokai", word_wrap=True)
    console.print(
        Panel(syntax, title=f"{proposal.provider}/{proposal.model}", border_style="green")
    )
    if proposal.danger.is_dangerous:
        console.print(
            Panel(
                "\n".join(f"⚠ {reason}" for reason in proposal.danger.reasons),
                title="[bold red]Potentially dangerous command[/bold red]",
                border_style="red",
            )
        )


def _render_system_info(snapshot: SystemInfoSnapshot) -> None:
    rows = [
        ("Operating System", snapshot.os_name),
        ("Shell", snapshot.shell),
        ("Current Directory", snapshot.cwd),
        ("Provider", snapshot.provider),
        ("Model", snapshot.model),
        ("Version", snapshot.version),
    ]
    label_width = max(len(label) for label, _ in rows)
    body = "\n".join(f"{label.ljust(label_width)} : {value}" for label, value in rows)
    console.print(Panel(body, title="System Information", border_style="cyan"))


def _handle_execution(session: TermiSession, proposal: CommandProposal) -> None:
    settings = session.settings_manager.settings

    should_confirm = settings.safe_mode and (
        proposal.danger.is_dangerous or not settings.auto_execute
    )
    if not settings.auto_execute and not proposal.danger.is_dangerous:
        should_confirm = True

    if should_confirm and not Confirm.ask(
        "Execute this command?", default=not proposal.danger.is_dangerous
    ):
        console.print("[yellow]Skipped.[/yellow]")
        return

    result = session.agent.execute_proposal(proposal)

    if result.stdout.strip():
        console.print(result.stdout.rstrip())
    if result.stderr.strip():
        console.print(f"[red]{result.stderr.rstrip()}[/red]")

    if result.succeeded:
        console.print(f"[green]✓ exit code {result.exit_code}[/green]")
    else:
        console.print(f"[red]✗ exit code {result.exit_code}[/red]")
        if Confirm.ask("Ask the AI to explain this failure?", default=True):
            with console.status("Diagnosing failure..."):
                diagnosis = session.agent.explain_failure(result)
            console.print(Panel(diagnosis, title="Diagnosis", border_style="yellow"))


def _handle_os_command(session: TermiSession) -> None:
    snapshot = session.agent.get_system_info_snapshot()
    console.print(f"Operating System: [bold]{snapshot.os_name}[/bold]")


def _handle_shell_command(session: TermiSession) -> None:
    snapshot = session.agent.get_system_info_snapshot()
    console.print(f"Shell: [bold]{snapshot.shell}[/bold]")


def _handle_provider_command(session: TermiSession, args: list[str]) -> None:
    if not args:
        console.print(
            f"Active provider: [bold]{session.provider_manager.provider_name}[/bold] "
            f"(model: {session.provider_manager.model})"
        )
        return

    if args[0] == "list":
        table = Table(title="Supported Providers")
        table.add_column("Name")
        table.add_column("Default Model")
        for name in SUPPORTED_PROVIDERS:
            table.add_row(name, DEFAULT_MODELS[name])
        console.print(table)
        return

    if args[0] == "set" and len(args) >= 2:
        new_provider = args[1]
        new_model = args[2] if len(args) >= 3 else None
        try:
            session.provider_manager.set_provider(new_provider, new_model)
        except TermiError as exc:
            console.print(f"[red]{exc}[/red]")
            return
        session.settings_manager.update(
            provider=session.provider_manager.provider_name,
            model=session.provider_manager.model,
        )
        console.print(
            f"[green]Provider switched to {session.provider_manager.provider_name} "
            f"({session.provider_manager.model})[/green]"
        )
        return

    console.print(
        "[yellow]Usage: /provider | /provider list | /provider set <name> [model][/yellow]"
    )


def _handle_history_command(session: TermiSession, args: list[str]) -> None:
    if args and args[0] == "clear":
        count = session.agent.history_repo.clear()
        console.print(f"[green]Cleared {count} history entries.[/green]")
        return

    entries = session.agent.history_repo.get_recent(limit=20)
    if not entries:
        console.print("[dim]No history yet.[/dim]")
        return

    table = Table(title="Recent History")
    table.add_column("ID")
    table.add_column("Prompt")
    table.add_column("Command")
    table.add_column("Status")
    table.add_column("Provider")
    for entry in reversed(entries):
        table.add_row(
            str(entry.id),
            entry.prompt,
            entry.command or "",
            entry.execution_status,
            f"{entry.provider}/{entry.model}",
        )
    console.print(table)


def _handle_settings_command(session: TermiSession, args: list[str]) -> None:
    if not args or args[0] == "show":
        settings = session.settings_manager.settings
        table = Table(title="Settings")
        table.add_column("Key")
        table.add_column("Value")
        for key, value in settings.to_dict().items():
            table.add_row(key, str(value))
        console.print(table)
        return

    if args[0] == "edit" and len(args) >= 3:
        key, raw_value = args[1], " ".join(args[2:])
        value: object = raw_value
        if raw_value.lower() in {"true", "false"}:
            value = raw_value.lower() == "true"
        elif raw_value.isdigit():
            value = int(raw_value)
        try:
            session.settings_manager.update(**{key: value})
        except TermiError as exc:
            console.print(f"[red]{exc}[/red]")
            return
        console.print(f"[green]Updated {key} = {value}[/green]")
        return

    console.print(
        "[yellow]Usage: /settings | /settings show | /settings edit <key> <value>[/yellow]"
    )


def _dispatch_slash_command(session: TermiSession, raw_input: str) -> bool:
    parts = raw_input.strip().split()
    command, args = parts[0], parts[1:]

    if command == "/exit":
        console.print("[cyan]Goodbye.[/cyan]")
        return True

    if command == "/help":
        _print_help()
    elif command == "/provider":
        _handle_provider_command(session, args)
    elif command == "/os":
        _handle_os_command(session)
    elif command == "/shell":
        _handle_shell_command(session)
    elif command == "/history":
        _handle_history_command(session, args)
    elif command == "/settings":
        _handle_settings_command(session, args)
    elif command == "/explain":
        if not args:
            console.print("[yellow]Usage: /explain <command>[/yellow]")
        else:
            with console.status("Explaining..."):
                explanation = session.agent.explain_command(" ".join(args))
            console.print(Panel(explanation, title="Explanation", border_style="blue"))
    elif command == "/retry":
        proposal = session.agent.retry_last()
        if proposal is None:
            console.print("[yellow]Nothing to retry yet.[/yellow]")
        else:
            _render_proposal(proposal)
            _handle_execution(session, proposal)
    else:
        console.print(f"[red]Unknown command: {command}[/red] Type /help for a list of commands.")

    return False


def _run_repl() -> None:
    session = TermiSession()
    _print_banner()

    while True:
        try:
            raw_input_text = console.input("[bold cyan]termi>[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not raw_input_text:
            continue

        if raw_input_text.startswith("/"):
            should_exit = _dispatch_slash_command(session, raw_input_text)
            if should_exit:
                break
            continue

        if detect_system_info_query(raw_input_text):
            snapshot = session.agent.get_system_info_snapshot()
            _render_system_info(snapshot)
            continue

        try:
            with console.status("Thinking..."):
                proposal = session.agent.generate_command(raw_input_text)
        except TermiError as exc:
            console.print(f"[red]Error: {exc}[/red]")
            continue

        _render_proposal(proposal)
        _handle_execution(session, proposal)

    session.database.close()


@app.command()
def main(
    prompt: list[str] = typer.Argument(  # noqa: B008 - required Typer pattern
        None, help="One-shot natural language request. If omitted, starts an interactive session."
    ),
) -> None:
    if prompt:
        session = TermiSession()
        joined_prompt = " ".join(prompt)

        if detect_system_info_query(joined_prompt):
            snapshot = session.agent.get_system_info_snapshot()
            _render_system_info(snapshot)
            session.database.close()
            return

        try:
            with console.status("Thinking..."):
                proposal = session.agent.generate_command(joined_prompt)
        except TermiError as exc:
            console.print(f"[red]Error: {exc}[/red]")
            session.database.close()
            raise typer.Exit(code=1) from exc

        _render_proposal(proposal)
        _handle_execution(session, proposal)
        session.database.close()
        return

    _run_repl()


def run() -> None:
    try:
        app()
    except Exception as exc:  # noqa: BLE001 - top-level safety net
        logger.exception("Unhandled error")
        console.print(f"[red]Unexpected error: {exc}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    run()