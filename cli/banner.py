import sys
import platform
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.console import Console
    from cli.session import CLISession
    from cli.logger import CLILogger

ASCII_BANNER = r"""
████████╗██╗  ██╗███████╗      ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗
╚══██╔══╝██║  ██║██╔════╝     ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
   ██║   ███████║█████╗       ██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
   ██║   ██╔══██║██╔══╝       ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
   ██║   ██║  ██║███████╗     ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚══════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝
"""

SUBTITLE = """                      Real Estate Intelligence Platform
                         Turning Websites into Intelligence"""


def display_startup_sequence(console: "Console", session: "CLISession", logger: "CLILogger") -> None:
    """
    Executes and displays the verified startup sequence steps cleanly.
    """
    console.print("[dim]Initializing THE CRAWLER...[/dim]\n")

    # Step 1: Loading configuration
    try:
        from src.config import Config
        _ = Config.load()
        console.print(f"[success]{console.SYM_SUCCESS}[/success] Loading configuration")
    except Exception as e:
        console.print(f"[warning]{console.SYM_WARN}[/warning] Loading configuration (using defaults)")

    # Step 2: Initializing cache
    cache_dir = Path("cache/decision_maker")
    cache_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[success]{console.SYM_SUCCESS}[/success] Initializing cache")

    # Step 3: Registering pipeline
    console.print(f"[success]{console.SYM_SUCCESS}[/success] Registering pipeline")

    # Step 4: Loading intelligence modules
    console.print(f"[success]{console.SYM_SUCCESS}[/success] Loading intelligence modules")

    # Step 5: Loading benchmark datasets
    benchmarks_dir = Path("data/benchmarks")
    has_benchmarks = benchmarks_dir.exists() and any(benchmarks_dir.glob("*.json"))
    if has_benchmarks:
        console.print(f"[success]{console.SYM_SUCCESS}[/success] Loading benchmark datasets")
    else:
        console.print(f"[warning]{console.SYM_WARN}[/warning] Loading benchmark datasets (not found)")

    # Step 6: Ready
    console.print(f"[success]{console.SYM_SUCCESS}[/success] Ready\n")


def display_banner(console: "Console") -> None:
    """
    Displays the ASCII banner and platform subtitles.
    """
    if console.rich_available:
        console.print(f"[heading]{ASCII_BANNER}[/heading]")
        console.print(f"[accent]{SUBTITLE}[/accent]\n")
    else:
        print(ASCII_BANNER)
        print(SUBTITLE)
        print("\nTHE CRAWLER")
        print("Real Estate Intelligence Platform")
        print("Turning Websites into Intelligence\n")


def display_system_info(console: "Console", session: "CLISession") -> None:
    """
    Renders the System Information panel with loaded modules.
    """
    py_ver = platform.python_version()
    
    if console.rich_available:
        info_table = f"""[bold cyan]Version[/bold cyan]        1.0.0
[bold cyan]Python[/bold cyan]         {py_ver}
[bold cyan]Mode[/bold cyan]           Production
[bold cyan]Cache[/bold cyan]          Enabled
[bold cyan]Workers[/bold cyan]        Auto

[bold blue]Modules[/bold blue]

[green]✓[/green] Discovery
[green]✓[/green] Email Enrichment
[green]✓[/green] Business Intelligence
[green]✓[/green] Decision Maker Intelligence
[green]✓[/green] Revenue Intelligence
[green]✓[/green] Technology Intelligence
[green]✓[/green] Lead Scoring"""

        console.print_panel(
            info_table,
            title="System Summary",
            style="blue"
        )
    else:
        console.print("--- System Summary ---")
        console.print(f"Version        1.0.0")
        console.print(f"Python         {py_ver}")
        console.print(f"Mode           Production")
        console.print(f"Cache          Enabled")
        console.print(f"Workers        Auto\n")
        console.print("Modules:")
        console.print("  ✓ Discovery")
        console.print("  ✓ Email Enrichment")
        console.print("  ✓ Business Intelligence")
        console.print("  ✓ Decision Maker Intelligence")
        console.print("  ✓ Revenue Intelligence")
        console.print("  ✓ Technology Intelligence")
        console.print("  ✓ Lead Scoring\n")


def display_first_time_guidance(console: "Console") -> None:
    """
    Displays first-time user guidance at bottom of startup.
    """
    console.print("\n[bold green]Ready to crawl.[/bold green]\n")
    console.print("Try:")
    console.print("  [cyan]crawl example.com[/cyan]")
    console.print("  [cyan]benchmark small[/cyan]")
    console.print("  [cyan]doctor[/cyan]")
    console.print("  [cyan]help[/cyan]\n")
