# Changelog

All notable changes to **THE CRAWLER** real estate intelligence platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-22

### Added
- **Interactive Developer CLI**: Full-featured interactive REPL (`crawler`) powered by `prompt_toolkit` and `rich`, featuring tab auto-completion, persistent command history, and custom prompt formatting.
- **Scriptable Non-Interactive Execution**: Support for direct command-line execution (`crawler crawl example.com`, `crawler benchmark small`, `crawler doctor`, `crawler status`, `crawler version`) matching developer tools like Git, Docker, and GitHub CLI.
- **7-Stage Intelligence Pipeline**:
  1. *Discovery*: Automated Google Maps scraping via Apify integration.
  2. *Email Enrichment*: Subpage crawling and heuristic contact email extraction.
  3. *Business Intelligence*: Multi-signal profiling of agent counts, office networks, and business operation models.
  4. *Decision Maker Intelligence*: Executive candidate scoring, role identification (Owners, Founders, Designated Brokers), and verified email matching.
  5. *Revenue Intelligence*: Multi-tier transaction volume and Gross Commission Income (GCI) estimations.
  6. *Technology Intelligence*: Automatic detection of CMS, IDX, CRM, analytics, and marketing stack.
  7. *Lead Scoring*: Weighted Opportunity Score computation (0-100) and tier assignment (Low Priority to High Priority).
- **Diagnostics & Health System (`doctor`)**: Environment readiness checker validating Python runtime, configuration, cache directories, logs, benchmark datasets, and pipeline registrations.
- **Runtime State Inspection (`status`)**: Operational state checker returning pipeline readiness, active cache size, worker counts, and session uptime.
- **Evaluation & Benchmark Framework (`benchmark`)**: Built-in benchmark engine executing precision, accuracy, latency, and memory profiling across dataset tiers (`small`, `medium`, `large`, `edge_cases`, `known_failures`).
- **Multi-Format Export Engine**: Automated export to standardized CSV, styled Excel workbooks (with custom color palettes and auto-wrapped columns), and Clay-compatible CSV format.
- **CLI Logging System**: ANSI-stripped file logger writing structured event records to `logs/cli.log`.
- **Package Configuration (`pyproject.toml`)**: Standardized Python packaging with optional `[cli]` extras.

### Verification & Testing
- 91 comprehensive unit tests covering models, validators, scrapers, deduplication, enrichment engines, scoring, export formats, and pipeline orchestrators.
- Initial benchmark reference baseline (`baseline_v1.0.json`) achieving 100% Decision Maker accuracy and email precision on the standard benchmark suite.
