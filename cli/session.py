import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class CLISession:
    """
    Tracks runtime statistics and state for an interactive or non-interactive CLI session.
    Powers the session exit summary.
    """
    start_time: float = 0.0
    start_dt: datetime = None
    commands_executed: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0
    benchmark_runs: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    warnings: int = 0
    errors: int = 0
    debug: bool = False
    banner_shown: bool = False
    is_interactive: bool = True

    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()
            self.start_dt = datetime.now()

    def record_command(self, name: str, success: bool = True) -> None:
        self.commands_executed += 1
        if not success:
            self.errors += 1

    def record_crawl(self, success: bool = True) -> None:
        if success:
            self.successful_crawls += 1
        else:
            self.failed_crawls += 1
            self.errors += 1

    def record_benchmark(self) -> None:
        self.benchmark_runs += 1

    def record_cache(self, hit: bool = True) -> None:
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_warning(self) -> None:
        self.warnings += 1

    def record_error(self) -> None:
        self.errors += 1

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def elapsed_formatted(self) -> str:
        total_secs = int(self.elapsed_seconds)
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        seconds = total_secs % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def total_crawls(self) -> int:
        return self.successful_crawls + self.failed_crawls

    @property
    def total_cache_accesses(self) -> int:
        return self.cache_hits + self.cache_misses

    @property
    def cache_hit_rate_pct(self) -> float:
        if self.total_cache_accesses == 0:
            return 0.0
        return round((self.cache_hits / self.total_cache_accesses) * 100.0, 1)

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "Duration": self.elapsed_formatted,
            "Commands Executed": self.commands_executed,
            "Successful Crawls": self.successful_crawls,
            "Failed Crawls": self.failed_crawls,
            "Benchmark Runs": self.benchmark_runs,
            "Warnings": self.warnings,
            "Errors": self.errors,
            "Cache Hit Rate": f"{self.cache_hit_rate_pct}%" if self.total_cache_accesses > 0 else "N/A"
        }
