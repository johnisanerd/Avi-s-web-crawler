# Real Estate Lead-Generation System

A modular, production-grade lead-generation system that scrapes residential real estate brokerages using the Apify Google Maps Scraper, normalizes the data, applies residential heuristics, deduplicates results using fuzzy logic (`rapidfuzz`), and exports to a premium formatted Excel spreadsheet.

## Prerequisites
- Python 3.12+
- An Apify API Token (configured in `.env`)

## Installation & Setup

1. **Clone/Navigate to the workspace**:
   ```bash
   cd C:\Users\RP\.gemini\antigravity-ide\scratch\real-estate-lead-generator
   ```

2. **Create a Python virtual environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - **Windows (Command Prompt)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**:
   - Copy `.env.template` to a new file named `.env`:
     ```bash
     copy .env.template .env
     ```
   - Open `.env` and fill in your `APIFY_API_TOKEN`.

---

## Running the Pipeline

To run the pipeline with defaults configured in `.env`:
```bash
python -m src.main
```

### CLI Overrides
You can override environmental parameters directly via command-line flags:
```bash
python -m src.main --queries "real estate agency, residential broker" --locations "Miami FL" --max-results 20 --output miami_leads.xlsx
```

---

## Running Verification Tests

To verify code correctness, you can run the suite of unit and integration tests using python's built-in `unittest` runner:
```bash
python -m unittest tests.test_pipeline
```
