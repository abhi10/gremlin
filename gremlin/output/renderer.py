"""Output rendering for different formats."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def render_rich(content: str, scope: str, console: Console) -> None:
    """Render output with Rich formatting.

    Args:
        content: Markdown content from Claude
        scope: Original scope string
        console: Rich console instance
    """
    console.print()
    console.print(Panel(f"[bold]Risk Scenarios for:[/bold] {scope}", expand=False))
    console.print()
    console.print(Markdown(content))


def render_markdown(content: str) -> None:
    """Render raw markdown output.

    Args:
        content: Markdown content from Claude
    """
    print(content)


def render_json(content: str) -> None:
    """Render JSON output.

    Args:
        content: Content from Claude (TODO: parse into structured JSON)
    """
    # TODO: Parse Claude's response into structured JSON
    # For now, just output the raw text
    print(content)
