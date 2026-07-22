import shlex
import sys
from typing import List, Tuple, Optional, TYPE_CHECKING

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.key_binding import KeyBindings
    PT_AVAILABLE = True
except ImportError:
    PT_AVAILABLE = False

if TYPE_CHECKING:
    from cli.console import Console
    from cli.history import CLIHistoryManager
    from cli.completion import CLICompleter


class CLIPromptManager:
    """
    Handles REPL input prompting, prompt_toolkit integration, keybindings,
    shell argument splitting (shlex), and fallback input handling.
    """

    def __init__(
        self,
        console: "Console",
        history_mgr: "CLIHistoryManager",
        completer: Optional["CLICompleter"] = None
    ):
        self.console = console
        self.history_mgr = history_mgr
        self.completer = completer
        self._pt_session = None

    def _init_pt_session(self) -> None:
        if PT_AVAILABLE and self._pt_session is None:
            try:
                bindings = KeyBindings()

                @bindings.add('c-l')
                def _clear_screen(event):
                    self.console.clear_screen()

                style = PTStyle.from_dict({
                    'prompt': '#00ff87 bold',
                    'pointer': '#00bfff bold'
                })

                pt_hist = self.history_mgr.get_pt_history()
                self._pt_session = PromptSession(
                    history=pt_hist,
                    completer=self.completer,
                    key_bindings=bindings,
                    style=style
                )
            except Exception:
                self._pt_session = False

    def get_input(self) -> str:
        """
        Prompts the user for input using prompt_toolkit if available, else input().
        Returns raw command input string.
        """
        prompt_text = "crawler > "
        self._init_pt_session()

        if PT_AVAILABLE and self._pt_session:

            try:
                # Custom prompt formatting for prompt_toolkit
                formatted_prompt = [
                    ('class:prompt', 'crawler'),
                    ('', ' '),
                    ('class:pointer', '>'),
                    ('', ' ')
                ]
                return self._pt_session.prompt(formatted_prompt)
            except KeyboardInterrupt:
                raise
            except EOFError:
                raise
        else:
            try:
                return input(prompt_text)
            except (KeyboardInterrupt, EOFError):
                raise

    @staticmethod
    def parse_command_line(line: str) -> Tuple[str, List[str]]:
        """
        Parses raw command line input using shlex to support quoted arguments.
        Returns tuple of (command_name, list_of_arguments).
        """
        line_clean = line.strip()
        if not line_clean:
            return "", []

        try:
            tokens = shlex.split(line_clean)
        except ValueError:
            # Handle unclosed quotes gracefully by splitting on whitespace
            tokens = line_clean.split()

        if not tokens:
            return "", []

        cmd_name = tokens[0].lower()
        args = tokens[1:]
        return cmd_name, args
