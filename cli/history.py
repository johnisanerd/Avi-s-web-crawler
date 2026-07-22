import os
from pathlib import Path
from typing import List, Optional

try:
    from prompt_toolkit.history import FileHistory as PTFileHistory
    PT_HISTORY_AVAILABLE = True
except ImportError:
    PT_HISTORY_AVAILABLE = False


class CLIHistoryManager:
    """
    Manages persistent command history across CLI sessions.
    Stores entries in logs/.crawler_history.
    """

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path("logs/.crawler_history")
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def get_pt_history(self):
        """
        Returns a prompt_toolkit FileHistory instance if prompt_toolkit is available.
        """
        if PT_HISTORY_AVAILABLE:
            return PTFileHistory(str(self.history_file))
        return None

    def load_history_list(self) -> List[str]:
        """
        Loads history entries from file as a list of strings.
        """
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            return lines
        except Exception:
            return []

    def append_history(self, command: str) -> None:
        """
        Appends a command to the history file if it's non-empty.
        """
        cmd = command.strip()
        if not cmd:
            return
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(cmd + "\n")
        except Exception:
            pass
