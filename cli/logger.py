import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)


class CLILogger:
    """
    Dedicated file logger for CLI operations.
    Appends clean, timestamped, ANSI-stripped log entries to logs/cli.log.
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path("logs/cli.log")
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _write(self, level: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_msg = strip_ansi(str(message))
        line = f"[{timestamp}] [{level.upper()}] {clean_msg}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def info(self, msg: str) -> None:
        self._write("INFO", msg)

    def warning(self, msg: str) -> None:
        self._write("WARN", msg)

    def error(self, msg: str, exc: Optional[Exception] = None) -> None:
        full_msg = f"{msg} | Error: {exc}" if exc else msg
        self._write("ERROR", full_msg)

    def debug(self, msg: str) -> None:
        self._write("DEBUG", msg)

    def log_startup(self, mode: str = "Interactive") -> None:
        self.info(f"--- CLI Session Started (Mode: {mode}, Python: {sys.version.split()[0]}, Platform: {sys.platform}) ---")

    def log_shutdown(self, duration: str, commands_cnt: int) -> None:
        self.info(f"--- CLI Session Ended (Duration: {duration}, Commands: {commands_cnt}) ---")

    def log_command(self, cmd_str: str) -> None:
        self.info(f"Command Executed: {cmd_str}")

    def log_crawl(self, target: str, status: str) -> None:
        self.info(f"Crawl Operation: target='{target}', status='{status}'")

    def log_benchmark(self, tier: str, status: str) -> None:
        self.info(f"Benchmark Execution: tier='{tier}', status='{status}'")
