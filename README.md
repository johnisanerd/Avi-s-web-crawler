# THE CRAWLER — Real Estate Intelligence Platform (v1.0.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/tests-91%20passing-brightgreen.svg)]()
[![Precision Baseline](https://img.shields.io/badge/precision-100%25-green.svg)]()

> **Turning Websites into Intelligence.**
> **Production-grade Real Estate Lead Generation & Executive Intelligence Pipeline.**

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Architecture & Pipeline Workflow](#-architecture--pipeline-workflow)
3. [Installation & Setup](#-installation--setup)
4. [CLI Usage Guide](#-cli-usage-guide)
   - [Interactive REPL Mode](#interactive-repl-mode)
   - [Scriptable Non-Interactive Mode](#scriptable-non-interactive-mode)
5. [CLI Command Reference](#-cli-command-reference)
6. [Configuration Reference](#-configuration-reference)
7. [Intelligence Modules Breakdown](#-intelligence-modules-breakdown)
8. [Benchmark & Evaluation Framework](#-benchmark--evaluation-framework)
9. [Diagnostics & Troubleshooting (`doctor`)](#-diagnostics--troubleshooting-doctor)
10. [Development & Testing Workflow](#-development--testing-workflow)

---

## 🚀 Overview

**THE CRAWLER** is a production-grade lead generation platform engineered specifically for the residential and commercial real estate domain. It combines automated geographic discovery via Google Maps with multi-stage web scraping, heuristic extraction, executive candidate scoring, revenue modeling, technology stack detection, and fuzzy deduplication.

### Key Capabilities

- 🤖 **7-Stage Intelligence Pipeline**: Automated discovery, email enrichment, business intelligence, decision maker identification, revenue estimation, tech stack detection, and weighted lead scoring.
- 💻 **Dual Execution CLI**: Ships with both an interactive REPL (`crawler`) with autocomplete & history, and a scriptable non-interactive CLI compatible with standard shell workflows.
- 🎯 **Decision Maker Intelligence**: Identifies primary decision makers (Owners, Founders, Designated Brokers, Managing Partners) and pairs them with verified business emails.
- 📊 **Multi-Format Export Engine**: Generates standard CSV, styled Excel workbooks (with custom color palettes and auto-wrapped columns), and Clay-compatible import CSVs.
- ⚡ **Benchmark Suite**: Integrated evaluator engine measuring precision, accuracy, latency, and memory performance across versioned benchmark tiers (`small`, `medium`, `large`, `edge_cases`, `known_failures`).

---

## 🏗 Architecture & Pipeline Workflow

```
+-----------------------------------------------------------------------------------+
|                                  THE CRAWLER CLI                                  |
|               Interactive REPL  |  Scriptable Non-Interactive Commands              |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        LEAD GENERATION PIPELINE ENGINE                            |
+-----------------------------------------------------------------------------------+
                                          |
  [Stage 1: Discovery] ------------> Apify Google Maps Scraper / URL Target
                                          |
  [Stage 2: Email Enrichment] -----> Subpage Web Crawler & Heuristic Email Matcher
                                          |
  [Stage 3: Business Intelligence]-> Agent Count, Office Network, Operations Profile
                                          |
  [Stage 4: DM Intelligence] -------> Executive Role Matcher & Email Verification
                                          |
  [Stage 5: Revenue Intelligence] -> Transaction Volume & GCI Estimation Engine
                                          |
  [Stage 6: Tech Intelligence] ----> CMS, IDX, CRM & Marketing Stack Detection
                                          |
  [Stage 7: Lead Scoring] ----------> Weighted Priority Scoring (0-100) & Tiering
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            MULTI-FORMAT EXPORT ENGINE                             |
|               Standard CSV  |  Styled Excel Workbook  |  Clay Import CSV          |
+-----------------------------------------------------------------------------------+
```

---

## 📥 Installation & Setup

### Prerequisites
- **Python 3.10+** (Python 3.11/3.12 recommended)
- **Git**

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/real-estate-lead-generator.git
   cd real-estate-lead-generator
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv

   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1

   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Install core dependencies & CLI framework
   pip install -e .[cli]
   ```

4. **Environment Configuration**:
   Copy `.env.template` to `.env` and configure your API tokens (optional for Apify live scraping):
   ```bash
   cp .env.template .env
   ```

---

## 💻 CLI Usage Guide

THE CRAWLER provides two ways to interact with the platform.

### Interactive REPL Mode

Launch the interactive REPL by running `crawler` without arguments:
```bash
python crawler.py
# or
python -m crawler
```

Output:
```text
Initializing THE CRAWLER...

✓ Loading configuration
✓ Initializing cache
✓ Registering pipeline
✓ Loading intelligence modules
✓ Loading benchmark datasets
✓ Ready

████████╗██╗  ██╗███████╗      ██████╗██████╗  █████╗ ██╗    ██╗██╗     ███████╗██████╗
╚══██╔══╝██║  ██║██╔════╝     ██╔════╝██╔══██╗██╔══██╗██║    ██║██║     ██╔════╝██╔══██╗
   ██║   ███████║█████╗       ██║     ██████╔╝███████║██║ █╗ ██║██║     █████╗  ██████╔╝
   ██║   ██╔══██║██╔══╝       ██║     ██╔══██╗██╔══██║██║███╗██║██║     ██╔══╝  ██╔══██╗
   ██║   ██║  ██║███████╗     ╚██████╗██║  ██║██║  ██║╚███╔███╔╝███████╗███████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚══════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝

                      Real Estate Intelligence Platform
                         Turning Websites into Intelligence

Ready to crawl.

Try:
  crawl example.com
  benchmark small
  doctor
  help

crawler > 
```

### Scriptable Non-Interactive Mode

Execute commands directly from scripts or terminal pipelines:
```bash
python crawler.py crawl apexrealty.com
python crawler.py benchmark small
python crawler.py doctor
python crawler.py status
python crawler.py version
```

---

## 📖 CLI Command Reference

| Command | Aliases | Syntax | Description | Exit Codes |
| :--- | :---: | :--- | :--- | :---: |
| `crawl` | `c` | `crawl <domain_or_url>` | Runs full 7-stage intelligence pipeline on a target domain. | 0 (success), 1 (error) |
| `batch` | `b` | `batch <file_path>` | Executes batch lead generation pipeline on an input file. | 0 (success), 1 (error) |
| `benchmark` | `bench` | `benchmark [tier]` | Executes quality benchmark suite on dataset tier (`small`, `medium`, `large`, `edge_cases`, `known_failures`). | 0 (success), 1 (error) |
| `stats` | `s` | `stats` | Displays session performance and runtime execution metrics. | 0 |
| `status` | - | `status` | Displays real-time operational state of THE CRAWLER. | 0 |
| `doctor` | - | `doctor` | Runs complete environment health and diagnostic checks. | 0 |
| `config` | - | `config [show \| get <key>]` | Displays loaded configuration or inspects specific setting keys. | 0 |
| `cache` | - | `cache [stats \| clear]` | Inspects domain enrichment cache disk usage or purges cached JSONs. | 0 |
| `version` | `ver`, `v` | `version` | Displays version, architecture, Python, and OS platform details. | 0 |
| `banner` | - | `banner` | Manually redisplays ASCII banner and System Summary card. | 0 |
| `clear` | `cls` | `clear` | Clears terminal screen. | 0 |
| `help` | `h`, `?` | `help [command]` | Displays command overview table or detailed help page. | 0 |
| `exit` | `quit`, `q`| `exit` | Terminates interactive CLI session and prints Session Summary. | 0 |

---

## ⚙ Configuration Reference

Configuration settings are loaded from environment variables (or `.env` file) via `src.config.Config`.

| Option Key | Default | Valid Range / Values | Description | Impact |
| :--- | :---: | :--- | :--- | :--- |
| `APIFY_API_TOKEN` | `""` | String | Apify API authentication token. | Required for live Google Maps scraping. |
| `APIFY_ACTOR_ID` | `compass/google-maps-extractor` | Valid Apify Actor ID | Target scraper actor on Apify platform. | Defines Apify scraper engine. |
| `DEFAULT_SEARCH_QUERIES` | `real estate agency, residential real estate broker` | Comma-separated strings | Initial search queries for lead discovery. | Controls search scope. |
| `DEFAULT_LOCATIONS` | `Miami FL, Tampa FL` | Comma-separated strings | Target geographical locations. | Controls geographic filtering. |
| `DEFAULT_MAX_RESULTS_PER_QUERY` | `50` | `1 - 500` | Max scraped places per location query. | Controls download volume. |
| `MIN_SIMILARITY_SCORE` | `85` | `0 - 100` | RapidFuzz similarity threshold for deduplication. | Higher values enforce stricter deduplication. |
| `LOG_LEVEL` | `INFO` | `DEBUG, INFO, WARNING, ERROR` | Application logging verbosity. | Controls log output detailedness. |
| `RAW_DATA_DIR` | `data/raw` | Valid directory path | Immutable raw JSON storage folder. | Stores raw scraper responses. |
| `OUTPUT_DATA_DIR` | `data/output` | Valid directory path | Formatted spreadsheet output folder. | Destination for exported Excel/CSVs. |
| `LOGS_DIR` | `logs` | Valid directory path | Log storage directory. | Destination for system and CLI logs. |

---

## 🧩 Intelligence Modules Breakdown

### 1. Discovery Engine (`src/scraper.py`)
Fetches raw lead records via Apify Google Maps Scraper or synthetic URL targets. Captures title, categories, address, phone, website, place ID, total score, and reviews count.

### 2. Email Enrichment Engine (`src/enrichment.py` & `src/email_extractor.py`)
Scans homepage and candidate subpages (`/contact`, `/about`, `/team`, `/agents`, `/staff`, `/brokers`) to extract domain-matched business emails and owner contact details using regex patterns and HTML block parsers.

### 3. Business Intelligence Engine (`src/business_intelligence.py`)
Profiles company size, office networks, and operation longevity. Estimates agent counts, office locations, and years in business by parsing team directories and structural indicators.

### 4. Decision Maker Intelligence Engine (`src/decision_maker_intelligence.py`)
Authoritative module for executive candidate scoring. Evaluates candidate titles (Owner, Founder, President, Managing Broker, Principal), weights evidence across page types, filters generic emails (`info@`, `support@`), and matches verified decision maker emails.

### 5. Revenue Intelligence Engine (`src/revenue_intelligence.py`)
Models financial metrics for real estate brokerages. Computes estimated deal transaction volume, estimated Gross Commission Income (GCI), and projected annual revenue ranges.

### 6. Technology Intelligence Engine (`src/technology_intelligence.py`)
Detects technology stack signatures across target websites, identifying Website CMS (WordPress, Squarespace, Wix), IDX Providers (KVCore, RealGeeks, iHomefinder), CRM Platforms, Analytics, and Chat providers.

### 7. Lead Scoring Engine (`src/lead_scorer.py`)
Calculates a unified Sales Opportunity Score (0-100) based on weighted factors (Decision Maker found +30, Verified email +20, Tech stack +15, Agent count +15, Revenue range +10, Rating/Reviews +10) and assigns priority tiers (`High Priority`, `Medium Priority`, `Low Priority`).

---

## 📊 Benchmark & Evaluation Framework

THE CRAWLER includes an evaluation framework (`src/evaluator.py`) to prevent quality regressions across version releases.

### Reference Baseline (v1.0.0)

| Metric | v1.0.0 Reference Baseline | Target Standard | Status |
| :--- | :---: | :---: | :---: |
| **Decision Maker Accuracy** | **100.0%** | `>= 95.0%` | PASS |
| **Email Verification Precision** | **100.0%** | `>= 98.0%` | PASS |
| **False Positive Rate** | **0.0%** | `<= 1.0%` | PASS |
| **False Negative Rate** | **0.0%** | `<= 5.0%` | PASS |
| **Average Processing Time** | **125.5 ms / lead** | `<= 250.0 ms` | PASS |
| **Peak Memory Usage** | **0.2 MB** | `<= 50.0 MB` | PASS |

### Running Benchmarks
```bash
python crawler.py benchmark small
python crawler.py benchmark edge_cases
```

Reports are automatically generated in `logs/`:
- `decision_maker_eval_report.json`
- `decision_maker_eval_report.md`
- `decision_maker_dashboard.html`

---

## 🩺 Diagnostics & Troubleshooting (`doctor`)

To run an instant health check on your environment, configuration, directories, and dependencies:
```bash
python crawler.py doctor
```

Example Output:
```text
SYSTEM DIAGNOSTICS & HEALTH CHECK
                         System Health Report                         
┌───────────────────────┬────────┬───────────────────────────────────┐
│ Component             │ Status │ Details / Suggested Fix           │
├───────────────────────┼────────┼───────────────────────────────────┤
│ Python Version        │ PASS   │ v3.11.9 (>= 3.10 required)        │
│ Configuration         │ PASS   │ Valid settings loaded             │
│ Cache Storage         │ PASS   │ cache\decision_maker exists       │
│ Logs Directory        │ PASS   │ logs ready                        │
│ Benchmark Datasets    │ PASS   │ data/benchmarks available         │
│ Data Directories      │ PASS   │ data/raw and data/output ready    │
│ Rich UI Framework     │ PASS   │ Installed                         │
│ Prompt Toolkit REPL   │ PASS   │ Installed                         │
│ Pipeline Registration │ PASS   │ 7 Intelligence Modules registered │
└───────────────────────┴────────┴───────────────────────────────────┘
```

---

## 🧪 Development & Testing Workflow

### Running Unit Tests

Run the complete suite of 91 automated unit tests using Python's built-in `unittest` runner:
```bash
python -m unittest discover tests
```

### Logs & Inspection
- **CLI Log**: `logs/cli.log` (ANSI-stripped event logs)
- **Pipeline Log**: `logs/pipeline.log`
- **Evaluator Log**: `logs/evaluator.log`

---

## 📄 License

THE CRAWLER is released under the [MIT License](LICENSE).
