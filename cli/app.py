import sys
import time
from typing import List, Optional

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from cli.session import CLISession
from cli.logger import CLILogger
from cli.console import Console
from cli.history import CLIHistoryManager
from cli.completion import CLICompleter
from cli.prompt import CLIPromptManager
from cli.banner import display_startup_sequence, display_banner, display_system_info, display_first_time_guidance
from cli.commands import register_all_commands


def display_exit_summary(console: Console, session: CLISession) -> None:
    """
    Renders the Session Exit Summary box cleanly upon termination.
    """

    s_dict = session.summary_dict()
    
    if console.rich_available:
        summary_lines = []
        for k, v in s_dict.items():
            summary_lines.append(f"[bold cyan]{k.ljust(22)}[/bold cyan] {v}")
        content = "\n".join(summary_lines)

        console.print_panel(
            content,
            title="Session Summary",
            style="cyan"
        )
    else:
        print("\n──────────────────────────────────────────")
        print("           Session Summary")
        print("──────────────────────────────────────────")
        for k, v in s_dict.items():
            print(f"  {k.ljust(22)} : {v}")
        print("──────────────────────────────────────────\n")

    console.print("[bold green]Thank you for using THE CRAWLER.[/bold green]")
    console.print("[dim]Goodbye.[/dim]\n")


def run_cli(sys_args: Optional[List[str]] = None) -> int:
    """
    Main application entry point orchestrator.
    Supports both interactive REPL mode and scriptable non-interactive execution mode.
    """
    if sys_args is None:
        sys_args = sys.argv[1:]

    # Check for debug mode flag
    debug_mode = "--debug" in sys_args
    clean_args = [a for a in sys_args if a != "--debug"]

    # Initialize core CLI infrastructure
    session = CLISession(debug=debug_mode)
    logger = CLILogger()
    console = Console()
    history_mgr = CLIHistoryManager()

    # Initialize Command Registry
    registry = register_all_commands()
    completer = CLICompleter(registry)
    prompt_mgr = CLIPromptManager(console, history_mgr, completer)

    # -------------------------------------------------------------
    # NON-INTERACTIVE EXECUTION MODE (e.g. crawler crawl example.com)
    # -------------------------------------------------------------
    if clean_args:
        session.is_interactive = False
        logger.log_startup(mode="Non-Interactive")
        cmd_name = clean_args[0].lower()
        cmd_args = clean_args[1:]

        cmd_obj = registry.get_command(cmd_name)
        if not cmd_obj:
            console.print_error(f"Unknown command: '{cmd_name}'")
            console.print("Type 'help' for available commands.")
            logger.log_shutdown(session.elapsed_formatted, session.commands_executed)
            return 1

        try:
            cmd_obj.handler(cmd_args, session, console, logger)
            logger.log_shutdown(session.elapsed_formatted, session.commands_executed)
            return 0
        except Exception as e:
            if debug_mode:
                raise
            console.print_error(f"Command '{cmd_name}' failed: {e}")
            logger.log_error(f"Command '{cmd_name}' failed", e)
            logger.log_shutdown(session.elapsed_formatted, session.commands_executed)
            return 1

    # -------------------------------------------------------------
    # INTERACTIVE REPL MODE (e.g. crawler)
    # -------------------------------------------------------------
    session.is_interactive = True
    logger.log_startup(mode="Interactive")

    # 1. Display Startup Sequence (< 1s)
    display_startup_sequence(console, session, logger)

    # 2. Display Banner & System Summary ONCE per session
    display_banner(console)
    session.banner_shown = True
    display_system_info(console, session)
    display_first_time_guidance(console)

    ctrl_c_counter = 0

    # 3. Interactive REPL Event Loop
    while True:
        try:
            raw_input = prompt_mgr.get_input()
            ctrl_c_counter = 0  # Reset Ctrl+C counter on successful input

            cmd_name, cmd_args = CLIPromptManager.parse_command_line(raw_input)
            if not cmd_name:
                continue

            # Record in history
            history_mgr.append_history(raw_input)

            # Check for exit command
            if cmd_name in ("exit", "quit", "q"):
                break

            # Dispatch command
            cmd_obj = registry.get_command(cmd_name)
            if cmd_obj:
                try:
                    cmd_obj.handler(cmd_args, session, console, logger)
                except Exception as e:
                    if debug_mode:
                        console.print_error(f"Execution traceback (debug mode enabled):")
                        import traceback
                        traceback.print_exc()
                    else:
                        console.print_error(f"Execution error: {e}")
                        console.print("[dim]Use --debug flag to see detailed stack trace.[/dim]")
                    session.record_error()
                    logger.log_error(f"Error in command '{cmd_name}'", e)
            else:
                console.print_error(f"Unknown command: '{cmd_name}'")
                console.print("Type 'help' for available commands.")
                session.record_warning()

        except KeyboardInterrupt:
            ctrl_c_counter += 1
            if ctrl_c_counter >= 2:
                console.print("\n[warning]Exiting session...[/warning]")
                break
            console.print("\n[warning]Operation cancelled. Press Ctrl+C again or type 'exit' to quit.[/warning]\n")
            continue
        except EOFError:
            console.print("\n[dim]EOF received. Exiting...[/dim]")
            break

    # 4. Clean Shutdown Sequence
    display_exit_summary(console, session)
    logger.log_shutdown(session.elapsed_formatted, session.commands_executed)
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
