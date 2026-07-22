import os
import sys
from typing import Any, List, Dict, Optional

# Detect Rich availability
try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.style import Style
    from rich.theme import Theme
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Detect Colorama availability for fallback
try:
    import colorama
    colorama.init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


class Console:
    """
    Unified Console rendering engine for THE CRAWLER CLI.
    Uses Rich for modern panels, tables, and colors if available.
    Degrades gracefully to colorama or plain text when unavailable.
    """

    # Visual indicators
    SYM_SUCCESS = "✓"
    SYM_INFO = "ℹ"
    SYM_WARN = "⚠"
    SYM_ERROR = "✖"
    SYM_BULLET = "●"

    def __init__(self):
        self.rich_available = RICH_AVAILABLE
        if self.rich_available:
            custom_theme = Theme({
                "success": "green bold",
                "info": "cyan",
                "warning": "yellow bold",
                "error": "red bold",
                "heading": "blue bold",
                "accent": "magenta bold",
                "dim": "dim"
            })
            self._rich_console = RichConsole(theme=custom_theme)
        else:
            self._rich_console = None

    def print(self, text: str = "", style: Optional[str] = None) -> None:
        if self.rich_available and self._rich_console:
            if style:
                self._rich_console.print(text, style=style)
            else:
                self._rich_console.print(text)
        else:
            # Plain text fallback
            print(text)

    def print_heading(self, text: str) -> None:
        if self.rich_available and self._rich_console:
            self._rich_console.print(f"\n[heading]{text}[/heading]")
        else:
            print(f"\n=== {text} ===")

    def print_success(self, text: str) -> None:
        msg = f"{self.SYM_SUCCESS} {text}"
        if self.rich_available and self._rich_console:
            self._rich_console.print(f"[success]{msg}[/success]")
        elif COLORAMA_AVAILABLE:
            print(f"{colorama.Fore.GREEN}{msg}{colorama.Style.RESET_ALL}")
        else:
            print(msg)

    def print_info(self, text: str) -> None:
        msg = f"{self.SYM_INFO} {text}"
        if self.rich_available and self._rich_console:
            self._rich_console.print(f"[info]{msg}[/info]")
        elif COLORAMA_AVAILABLE:
            print(f"{colorama.Fore.CYAN}{msg}{colorama.Style.RESET_ALL}")
        else:
            print(msg)

    def print_warning(self, text: str) -> None:
        msg = f"{self.SYM_WARN} {text}"
        if self.rich_available and self._rich_console:
            self._rich_console.print(f"[warning]{msg}[/warning]")
        elif COLORAMA_AVAILABLE:
            print(f"{colorama.Fore.YELLOW}{msg}{colorama.Style.RESET_ALL}")
        else:
            print(msg)

    def print_error(self, text: str) -> None:
        msg = f"{self.SYM_ERROR} {text}"
        if self.rich_available and self._rich_console:
            self._rich_console.print(f"[error]{msg}[/error]")
        elif COLORAMA_AVAILABLE:
            print(f"{colorama.Fore.RED}{msg}{colorama.Style.RESET_ALL}")
        else:
            print(msg)

    def print_panel(self, content: str, title: Optional[str] = None, subtitle: Optional[str] = None, style: str = "blue") -> None:
        if self.rich_available and self._rich_console:
            p = Panel(
                content,
                title=f"[bold]{title}[/bold]" if title else None,
                subtitle=f"[dim]{subtitle}[/dim]" if subtitle else None,
                border_style=style,
                padding=(1, 2)
            )
            self._rich_console.print(p)
        else:
            border = "─" * 55
            print(f"\n┌{border}┐")
            if title:
                print(f"│  {title.center(51)}  │")
                print(f"├{border}┤")
            for line in content.splitlines():
                print(f"│  {line.ljust(51)}  │")
            if subtitle:
                print(f"├{border}┤")
                print(f"│  {subtitle.center(51)}  │")
            print(f"└{border}┘\n")

    def print_table(self, title: str, headers: List[str], rows: List[List[Any]]) -> None:
        if self.rich_available and self._rich_console:
            table = Table(title=title, box=box.ROUNDED, header_style="cyan bold")
            for h in headers:
                table.add_column(h)
            for row in rows:
                table.add_row(*[str(item) for item in row])
            self._rich_console.print(table)
        else:
            print(f"\n--- {title} ---")
            header_line = " | ".join(str(h) for h in headers)
            print(header_line)
            print("-" * len(header_line))
            for row in rows:
                print(" | ".join(str(item) for item in row))
            print()

    def clear_screen(self) -> None:
        if self.rich_available and self._rich_console:
            self._rich_console.clear()
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
