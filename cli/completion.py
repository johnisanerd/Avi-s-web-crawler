from typing import List, TYPE_CHECKING

try:
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    PT_COMPLETER_AVAILABLE = True
except ImportError:
    PT_COMPLETER_AVAILABLE = False
    Completer = object

if TYPE_CHECKING:
    from cli.commands import CommandRegistry


class CLICompleter(Completer):
    """
    Dynamic tab completion provider for prompt_toolkit REPL.
    Inspected live from the CommandRegistry.
    """

    def __init__(self, registry: "CommandRegistry"):
        self.registry = registry

    def get_completions(self, document, complete_event):
        if not PT_COMPLETER_AVAILABLE:
            return

        text = document.text_before_cursor
        words = text.lstrip().split()
        
        # Current word being typed
        word_at_cursor = document.get_word_before_cursor()

        # Completing command at start of line
        if len(words) <= 1 and not text.endswith(" "):
            completions = set()
            for cmd in self.registry.commands.values():
                completions.add(cmd.name)
                for alias in cmd.aliases:
                    completions.add(alias)

            for c in sorted(completions):
                if c.startswith(word_at_cursor):
                    yield Completion(c, start_position=-len(word_at_cursor))
        else:
            # Subcommand or option completion
            first_cmd = words[0].lower()
            cmd_obj = self.registry.get_command(first_cmd)
            if cmd_obj and cmd_obj.autocomplete:
                for sub in cmd_obj.autocomplete:
                    if sub.startswith(word_at_cursor):
                        yield Completion(sub, start_position=-len(word_at_cursor))
