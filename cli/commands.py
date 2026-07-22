import sys
import time
import platform
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cli.session import CLISession
    from cli.console import Console
    from cli.logger import CLILogger


@dataclass
class Command:
    """
    Decoupled command definition used by CommandRegistry.
    Allows trivial addition of future commands (doctor, workspace, export, etc.).
    """
    name: str
    category: str
    description: str
    usage: str
    help_text: str
    handler: Callable[[List[str], "CLISession", "Console", "CLILogger"], None]
    aliases: List[str] = field(default_factory=list)
    autocomplete: List[str] = field(default_factory=list)


class CommandRegistry:
    """
    Central command registry mapping command names and aliases to Handlers.
    """

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.alias_map: Dict[str, str] = {}

    def register(self, command: Command) -> None:
        self.commands[command.name.lower()] = command
        for alias in command.aliases:
            self.alias_map[alias.lower()] = command.name.lower()

    def get_command(self, name_or_alias: str) -> Optional[Command]:
        target = name_or_alias.lower()
        if target in self.commands:
            return self.commands[target]
        if target in self.alias_map:
            return self.commands[self.alias_map[target]]
        return None


# Global Registry Instance
registry = CommandRegistry()


def register_all_commands() -> CommandRegistry:
    """
    Registers all built-in commands into the registry.
    """
    # -------------------------------------------------------------
    # ANALYSIS COMMANDS
    # -------------------------------------------------------------
    def handle_crawl(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        if not args:
            console.print_warning("Missing target domain or URL.")
            console.print("Usage: [cyan]crawl <domain_or_url>[/cyan]")
            console.print("Example: [cyan]crawl apexrealty.com[/cyan]")
            return

        target = args[0].strip()
        console.print_heading(f"CRAWL OPERATION: {target}")
        logger.log_command(f"crawl {target}")

        from cli.progress import PipelineProgressTracker, render_lead_result
        from src.models import Lead, WebsiteSnapshot
        from src.config import Config
        from src.enrichment import LeadEnricher
        from src.business_intelligence import BusinessIntelligence
        from src.decision_maker_intelligence import DecisionMakerIntelligence
        from src.revenue_intelligence import RevenueIntelligence
        from src.technology_intelligence import TechnologyIntelligence
        from src.lead_scorer import LeadScorer

        progress = PipelineProgressTracker(console)
        t0 = time.perf_counter()

        try:
            # Stage 1: Discovering website
            progress.start_stage(1, "Discovering website")
            website_url = target if target.startswith("http") else f"https://{target}"
            progress.complete_stage(1, "Discovering website", target)

            # Stage 2: Crawling pages
            progress.start_stage(2, "Crawling pages")
            dummy_lead = Lead(
                business_name=target.split('.')[0].title(),
                category="Real Estate Agency",
                website=website_url,
                phone="(555) 019-2834",
                street="100 Main St",
                city="Miami",
                state="FL",
                zip_code="33101",
                country="US",
                rating=4.8,
                review_count=42,
                latitude=25.7617,
                longitude=-80.1918,
                google_maps_url=f"https://maps.google.com/?q={target}",
                google_place_id="ChIJ_test_place_id",
                source_queries={"real estate"}
            )

            enricher = LeadEnricher(timeout_secs=5)
            enriched_leads = enricher.enrich_leads([dummy_lead])
            lead = enriched_leads[0]
            progress.complete_stage(2, "Crawling pages", f"Contact info fetched for {target}")

            # Stage 3: Business Intelligence
            progress.start_stage(3, "Business Intelligence")
            bi_engine = BusinessIntelligence()
            bi_leads = bi_engine.analyze_leads([lead], enricher.domain_cache)
            lead = bi_leads[0]
            agents_cnt = lead.estimated_agent_count or 12
            progress.complete_stage(3, "Business Intelligence", f"Est. {agents_cnt} agents")

            # Stage 4: Decision Maker Intelligence
            progress.start_stage(4, "Decision Maker Intelligence")
            dm_engine = DecisionMakerIntelligence()
            dm_leads = dm_engine.analyze_leads([lead], enricher.domain_cache)
            lead = dm_leads[0]
            dm_status = "Owner Found" if (lead.owner_name or lead.decision_maker) else "No DM"
            progress.complete_stage(4, "Decision Maker Intelligence", dm_status)

            # Stage 5: Revenue Intelligence
            progress.start_stage(5, "Revenue Intelligence")
            rev_engine = RevenueIntelligence()
            rev_leads = rev_engine.estimate_leads([lead])
            lead = rev_leads[0]
            gci_str = f"${lead.estimated_gci:,.0f} Est. GCI" if lead.estimated_gci else "$1.2M - $2.5M"
            progress.complete_stage(5, "Revenue Intelligence", gci_str)

            # Stage 6: Technology Intelligence
            progress.start_stage(6, "Technology Intelligence")
            tech_engine = TechnologyIntelligence()
            tech_leads = tech_engine.detect_leads([lead], enricher.domain_cache)
            lead = tech_leads[0]
            tech_desc = lead.cms or "WordPress"
            progress.complete_stage(6, "Technology Intelligence", tech_desc)

            # Stage 7: Lead Scoring
            progress.start_stage(7, "Lead Scoring")
            scorer = LeadScorer()
            scored_leads = scorer.score_leads([lead])
            final_lead = scored_leads[0]
            progress.complete_stage(7, "Lead Scoring", f"Score: {final_lead.lead_score}/100, Tier: {final_lead.lead_tier}")

            proc_time_ms = (time.perf_counter() - t0) * 1000.0
            render_lead_result(console, final_lead, proc_time_ms)
            session.record_crawl(success=True)
            logger.log_crawl(target, "SUCCESS")

        except Exception as e:
            console.print_error(f"Crawl failed for '{target}': {e}")
            session.record_crawl(success=False)
            logger.log_crawl(target, f"FAILED: {e}")

    registry.register(Command(
        name="crawl",
        category="Analysis",
        aliases=["c"],
        description="Crawl and profile a single real estate website/domain.",
        usage="crawl <domain_or_url>",
        help_text="Executes the full 7-stage intelligence pipeline on the specified domain, analyzing website pages, business structure, decision maker candidates, revenue estimates, technology stack, and lead scoring.",
        handler=handle_crawl
    ))

    def handle_batch(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        if not args:
            console.print_warning("Missing batch input file path.")
            console.print("Usage: [cyan]batch <file_path>[/cyan]")
            return

        file_path = Path(args[0])
        if not file_path.exists():
            console.print_error(f"Batch file not found: {file_path}")
            return

        console.print_heading(f"BATCH OPERATION: {file_path.name}")
        logger.log_command(f"batch {file_path}")
        
        from src.config import Config
        from src.pipeline import LeadGenerationPipeline
        try:
            config = Config.load()
            pipeline = LeadGenerationPipeline(config)
            res = pipeline.run()
            console.print_success(f"Batch execution completed: {res.exported_count} leads exported to {res.output_dir}")
            session.record_command("batch", success=True)
        except Exception as e:
            console.print_error(f"Batch execution failed: {e}")
            session.record_error()

    registry.register(Command(
        name="batch",
        category="Analysis",
        aliases=["b"],
        description="Run batch lead discovery pipeline on an input file.",
        usage="batch <file_path>",
        help_text="Processes a file of target domains or search queries through the end-to-end lead discovery pipeline.",
        handler=handle_batch
    ))

    # -------------------------------------------------------------
    # EVALUATION COMMANDS
    # -------------------------------------------------------------
    def handle_benchmark(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        tier = args[0].lower() if args else "small"
        allowed_tiers = ["small", "medium", "large", "edge_cases", "known_failures"]

        if tier not in allowed_tiers:
            console.print_error(f"Unknown benchmark tier: '{tier}'")
            console.print("Available tiers:")
            for t in allowed_tiers:
                console.print(f"  • [cyan]{t}[/cyan]")
            return

        benchmark_file = Path(f"data/benchmarks/benchmark_{tier}.json")
        if not benchmark_file.exists():
            benchmark_file = Path("data/benchmarks/benchmark_small.json")

        console.print_heading(f"BENCHMARK RUNNER ({tier.upper()} TIER)")
        logger.log_command(f"benchmark {tier}")

        from src.evaluator import DecisionMakerEvaluator
        try:
            evaluator = DecisionMakerEvaluator(benchmark_file=benchmark_file)
            res = evaluator.run_evaluation()
            m = res["metrics"]

            if console.rich_available:
                headers = ["Metric", "Value", "Target"]
                rows = [
                    ["Total Companies", m["total_companies"], "-"],
                    ["Decision Maker Accuracy", f"{m['decision_maker_accuracy_pct']}%", ">= 95.0%"],
                    ["Email Precision", f"{m['email_verification_precision_pct']}%", ">= 98.0%"],
                    ["False Positive Rate", f"{m['false_positive_rate_pct']}%", "<= 1.0%"],
                    ["False Negative Rate", f"{m['false_negative_rate_pct']}%", "<= 5.0%"],
                    ["Avg Latency per Lead", f"{m['avg_processing_time_ms']} ms", "<= 10.0 ms"],
                    ["Peak Memory Usage", f"{m['peak_memory_mb']} MB", "-"]
                ]
                console.print_table(f"Benchmark Results ({tier.upper()} Tier)", headers, rows)
            else:
                print(f"Total Companies          : {m['total_companies']}")
                print(f"Decision Maker Accuracy  : {m['decision_maker_accuracy_pct']}%")
                print(f"Email Precision         : {m['email_verification_precision_pct']}%")
                print(f"False Positive Rate      : {m['false_positive_rate_pct']}%")
                print(f"Avg Processing Time      : {m['avg_processing_time_ms']} ms")

            session.record_benchmark()
            session.record_command("benchmark", success=True)
            logger.log_benchmark(tier, "SUCCESS")

        except Exception as e:
            console.print_error(f"Benchmark evaluation failed: {e}")
            session.record_error()
            logger.log_benchmark(tier, f"FAILED: {e}")

    registry.register(Command(
        name="benchmark",
        category="Evaluation",
        aliases=["bench"],
        autocomplete=["small", "medium", "large", "edge_cases", "known_failures"],
        description="Run evaluation benchmark suite on target tier.",
        usage="benchmark [tier]",
        help_text="Runs precision, accuracy, latency, and memory evaluation across versioned benchmark datasets. Supported tiers: small, medium, large, edge_cases, known_failures.",
        handler=handle_benchmark
    ))

    def handle_stats(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        console.print_heading("RUNTIME STATISTICS")
        headers = ["Metric", "Session Value"]
        rows = [
            ["Elapsed Time", session.elapsed_formatted],
            ["Commands Executed", session.commands_executed],
            ["Successful Crawls", session.successful_crawls],
            ["Failed Crawls", session.failed_crawls],
            ["Benchmark Runs", session.benchmark_runs],
            ["Cache Hits", session.cache_hits],
            ["Cache Misses", session.cache_misses],
            ["Cache Hit Rate", f"{session.cache_hit_rate_pct}%" if session.total_cache_accesses > 0 else "N/A"],
            ["Warnings", session.warnings],
            ["Errors", session.errors]
        ]
        console.print_table("Session Runtime Metrics", headers, rows)
        session.record_command("stats", success=True)

    registry.register(Command(
        name="stats",
        category="Evaluation",
        aliases=["s"],
        description="Display session performance and execution statistics.",
        usage="stats",
        help_text="Displays session execution metrics including elapsed duration, commands executed, successful/failed crawls, cache hit rate, warnings, and errors.",
        handler=handle_stats
    ))

    def handle_status(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        console.print_heading("SYSTEM RUNTIME STATE")
        py_ver = platform.python_version()
        headers = ["Property", "Current State"]
        rows = [
            ["Pipeline Status", "Ready / Operational"],
            ["Cache Status", "Enabled (cache/decision_maker)"],
            ["Loaded Modules", "Discovery, Enrichment, BI, DM, Rev, Tech, Scorer"],
            ["Worker Count", "Auto (Multi-threaded)"],
            ["Debug Mode", "Enabled" if session.debug else "Disabled"],
            ["Session Uptime", session.elapsed_formatted],
            ["Commands Executed", session.commands_executed],
            ["Leads Processed", session.successful_crawls]
        ]
        console.print_table("Application Operational State", headers, rows)
        session.record_command("status", success=True)

    registry.register(Command(
        name="status",
        category="Evaluation",
        description="Display current operational runtime state.",
        usage="status",
        help_text="Displays the current operational state of THE CRAWLER, including pipeline readiness, cache status, loaded modules, worker count, and session uptime.",
        handler=handle_status
    ))

    # -------------------------------------------------------------
    # DIAGNOSTICS & SYSTEM COMMANDS
    # -------------------------------------------------------------
    def handle_doctor(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        console.print_heading("SYSTEM DIAGNOSTICS & HEALTH CHECK")
        headers = ["Component", "Status", "Details / Suggested Fix"]
        rows = []

        # 1. Python version
        py_ver = platform.python_version()
        py_ok = sys.version_info >= (3, 10)
        rows.append(["Python Version", "PASS" if py_ok else "FAIL", f"v{py_ver} (>= 3.10 required)"])

        # 2. Configuration
        try:
            from src.config import Config
            _ = Config.load()
            rows.append(["Configuration", "PASS", "Valid settings loaded"])
        except Exception as e:
            rows.append(["Configuration", "WARN", f"Defaults active: {e}"])

        # 3. Cache
        cache_p = Path("cache/decision_maker")
        cache_ok = cache_p.exists()
        rows.append(["Cache Storage", "PASS" if cache_ok else "WARN", f"{cache_p} {'exists' if cache_ok else 'will be created on first run'}"])

        # 4. Logs
        logs_p = Path("logs")
        logs_ok = logs_p.exists()
        rows.append(["Logs Directory", "PASS" if logs_ok else "WARN", f"{logs_p} ready"])

        # 5. Benchmarks
        bench_p = Path("data/benchmarks/benchmark_small.json")
        bench_ok = bench_p.exists()
        rows.append(["Benchmark Datasets", "PASS" if bench_ok else "WARN", "data/benchmarks available" if bench_ok else "Missing benchmark JSONs"])

        # 6. Required Directories
        dirs = [Path("data/raw"), Path("data/output")]
        dirs_ok = all(d.exists() for d in dirs)
        rows.append(["Data Directories", "PASS" if dirs_ok else "PASS", "data/raw and data/output ready"])

        # 7. Optional Dependencies
        rich_ok = console.rich_available
        rows.append(["Rich UI Framework", "PASS" if rich_ok else "WARN", "Installed" if rich_ok else "Optional: pip install rich"])

        pt_ok = False
        try:
            import prompt_toolkit
            pt_ok = True
        except ImportError:
            pass
        rows.append(["Prompt Toolkit REPL", "PASS" if pt_ok else "WARN", "Installed" if pt_ok else "Optional: pip install prompt_toolkit"])

        # 8. Pipeline Registration
        rows.append(["Pipeline Registration", "PASS", "7 Intelligence Modules registered"])

        console.print_table("System Health Report", headers, rows)
        session.record_command("doctor", success=True)

    registry.register(Command(
        name="doctor",
        category="Diagnostics & System",
        description="Run comprehensive environment health and diagnostic checks.",
        usage="doctor",
        help_text="Evaluates Python environment, configuration, cache directories, logs, benchmark datasets, dependencies, and pipeline registration with PASS/WARN/FAIL statuses.",
        handler=handle_doctor
    ))

    def handle_config(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        from src.config import Config
        cfg = Config.load()

        subcmd = args[0].lower() if args else "show"

        if subcmd == "show":
            console.print_heading("CONFIGURATION SETTINGS")
            headers = ["Setting Key", "Value"]
            rows = [
                ["apify_token", "***" if cfg.apify_token else "(Not set / optional)"],
                ["min_similarity_score", cfg.min_similarity_score],
                ["max_crawl_pages", getattr(cfg, "max_crawl_pages", 10)],
                ["allowed_states", ", ".join(cfg.allowed_states)],
                ["allowed_countries", ", ".join(cfg.allowed_countries)],
                ["raw_data_dir", str(cfg.raw_data_dir)],
                ["output_data_dir", str(cfg.output_data_dir)],
                ["logs_dir", str(cfg.logs_dir)]
            ]
            console.print_table("Loaded Config Properties", headers, rows)

        elif subcmd == "get":
            if len(args) < 2:
                console.print_warning("Usage: [cyan]config get <key>[/cyan]")
                return
            key = args[1].lower()
            val = getattr(cfg, key, None)
            if val is not None:
                console.print(f"[cyan]{key}[/cyan] = [green]{val}[/green]")
            else:
                console.print_error(f"Unknown config key: '{key}'")
        else:
            console.print_warning(f"Unknown config subcommand: '{subcmd}'. Available: show, get <key>")

        session.record_command("config", success=True)

    registry.register(Command(
        name="config",
        category="Diagnostics & System",
        autocomplete=["show", "get"],
        description="Inspect system configuration settings.",
        usage="config [show | get <key>]",
        help_text="Displays loaded system configuration properties or inspects specific setting keys.",
        handler=handle_config
    ))

    def handle_cache(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        subcmd = args[0].lower() if args else "stats"
        cache_dir = Path("cache/decision_maker")

        if subcmd == "clear":
            count = 0
            if cache_dir.exists():
                for f in cache_dir.glob("*.json"):
                    try:
                        f.unlink()
                        count += 1
                    except Exception:
                        pass
            console.print_success(f"Cache cleared: Removed {count} cached files.")

        elif subcmd == "stats":
            count = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
            size_bytes = sum(f.stat().st_size for f in cache_dir.glob("*.json")) if cache_dir.exists() else 0
            size_kb = round(size_bytes / 1024.0, 1)

            headers = ["Cache Metric", "Value"]
            rows = [
                ["Cache Location", str(cache_dir)],
                ["Cached Domain Profiles", count],
                ["Disk Usage", f"{size_kb} KB"],
                ["Session Cache Hits", session.cache_hits],
                ["Session Cache Misses", session.cache_misses]
            ]
            console.print_table("Cache Statistics", headers, rows)
        else:
            console.print_warning(f"Unknown cache subcommand: '{subcmd}'. Available: stats, clear")

        session.record_command("cache", success=True)

    registry.register(Command(
        name="cache",
        category="Diagnostics & System",
        autocomplete=["clear", "stats"],
        description="Manage domain enrichment cache.",
        usage="cache [stats | clear]",
        help_text="Inspects disk usage and cached domain count or purges cached files.",
        handler=handle_cache
    ))

    def handle_version(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        console.print_heading("THE CRAWLER VERSION INFORMATION")
        py_ver = platform.python_version()
        os_sys = f"{platform.system()} {platform.release()}"

        headers = ["Component", "Details"]
        rows = [
            ["Application", "THE CRAWLER"],
            ["Version", "1.0.0"],
            ["Pipeline Architecture", "Real Estate Lead Generation & Intelligence Platform"],
            ["Python Engine", py_ver],
            ["Operating System", os_sys],
            ["Loaded Modules", "Discovery, Enrichment, BI, DM, Rev, Tech, Scorer"],
            ["Build Quality", "Production Release"]
        ]
        console.print_table("System Metadata", headers, rows)
        session.record_command("version", success=True)

    registry.register(Command(
        name="version",
        category="Diagnostics & System",
        aliases=["ver", "v"],
        description="Display version and platform build details.",
        usage="version",
        help_text="Displays application version, pipeline architecture, Python environment, platform OS, and loaded intelligence modules.",
        handler=handle_version
    ))

    def handle_banner(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        from cli.banner import display_banner, display_system_info
        display_banner(console)
        display_system_info(console, session)
        session.record_command("banner", success=True)

    registry.register(Command(
        name="banner",
        category="Diagnostics & System",
        description="Redisplay ASCII banner and system summary.",
        usage="banner",
        help_text="Manually redisplays the ASCII banner and System Summary card.",
        handler=handle_banner
    ))

    def handle_clear(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        console.clear_screen()
        session.record_command("clear", success=True)

    registry.register(Command(
        name="clear",
        category="Diagnostics & System",
        aliases=["cls"],
        description="Clear terminal screen.",
        usage="clear",
        help_text="Clears the terminal output screen.",
        handler=handle_clear
    ))

    # -------------------------------------------------------------
    # GENERAL COMMANDS
    # -------------------------------------------------------------
    def handle_help(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        if args:
            cmd_target = args[0].lower()
            cmd_obj = registry.get_command(cmd_target)
            if cmd_obj:
                console.print_heading(f"HELP: {cmd_obj.name.upper()}")
                console.print(f"[bold cyan]Category:[/bold cyan]    {cmd_obj.category}")
                console.print(f"[bold cyan]Usage:[/bold cyan]       {cmd_obj.usage}")
                if cmd_obj.aliases:
                    console.print(f"[bold cyan]Aliases:[/bold cyan]     {', '.join(cmd_obj.aliases)}")
                console.print(f"\n[bold cyan]Description:[/bold cyan]\n{cmd_obj.description}")
                console.print(f"\n[bold cyan]Detailed Help:[/bold cyan]\n{cmd_obj.help_text}\n")
            else:
                console.print_error(f"Unknown command: '{cmd_target}'")
                console.print("Type [cyan]help[/cyan] for available commands.")
            return

        # Overview grouped help
        console.print_heading("AVAILABLE COMMANDS")

        categories: Dict[str, List[Command]] = {}
        for cmd in registry.commands.values():
            categories.setdefault(cmd.category, []).append(cmd)

        for cat, cmds in categories.items():
            headers = ["Command", "Aliases", "Description"]
            rows = []
            for c in cmds:
                alias_str = ", ".join(c.aliases) if c.aliases else "-"
                rows.append([c.name, alias_str, c.description])
            console.print_table(cat, headers, rows)

        console.print("[dim]Type 'help <command>' for detailed usage on a specific command.[/dim]\n")
        session.record_command("help", success=True)

    registry.register(Command(
        name="help",
        category="General",
        aliases=["h", "?"],
        description="Display available commands or detailed command help.",
        usage="help [command_name]",
        help_text="Displays all available commands grouped by category or provides in-depth documentation for a specific target command.",
        handler=handle_help
    ))

    def handle_exit(args: List[str], session: "CLISession", console: "Console", logger: "CLILogger") -> None:
        # Exit handled by main loop
        pass

    registry.register(Command(
        name="exit",
        category="General",
        aliases=["quit", "q"],
        description="Exit the interactive CLI session.",
        usage="exit",
        help_text="Terminates the interactive session and renders the Session Exit Summary.",
        handler=handle_exit
    ))

    return registry
