import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dotenv import load_dotenv

from src.constants import (
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    OUTPUT_DATA_DIR,
    LOGS_DIR,
    CLEANED_CSV_FILENAME,
    CLEANED_XLSX_FILENAME,
    CLAY_CSV_FILENAME,
    DEFAULT_SEARCH_QUERIES,
    DEFAULT_LOCATIONS,
    DEFAULT_MAX_RESULTS_PER_QUERY,
    DEFAULT_TIMEOUT_MINS,
    DEFAULT_MIN_SIMILARITY_SCORE
)


@dataclass(frozen=True, slots=True)
class Config:
    """
    Holds immutable system configuration settings.
    Guarantees thread-safe configuration values.
    """
    apify_token: str
    apify_actor_id: str
    search_queries: List[str]
    locations: List[str]
    max_results_per_query: int
    timeout_mins: int
    retry_count: int
    log_level: str
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    output_data_dir: Path
    logs_dir: Path
    cleaned_csv_name: str
    cleaned_xlsx_name: str
    clay_csv_name: str
    min_similarity_score: int
    excel_theme_color: str

    @property
    def allowed_states(self) -> Set[str]:
        """
        Derives the set of allowed states (both abbreviations and full names)
        from the locations configuration list.
        """
        us_states_map = {
            "AL": "ALABAMA", "AK": "ALASKA", "AZ": "ARIZONA", "AR": "ARKANSAS", "CA": "CALIFORNIA",
            "CO": "COLORADO", "CT": "CONNECTICUT", "DE": "DELAWARE", "FL": "FLORIDA", "GA": "GEORGIA",
            "HI": "HAWAII", "ID": "IDAHO", "IL": "ILLINOIS", "IN": "INDIANA", "IA": "IOWA",
            "KS": "KANSAS", "KY": "KENTUCKY", "LA": "LOUISIANA", "ME": "MAINE", "MD": "MARYLAND",
            "MA": "MASSACHUSETTS", "MI": "MICHIGAN", "MN": "MINNESOTA", "MS": "MISSISSIPPI", "MO": "MISSOURI",
            "MT": "MONTANA", "NE": "NEBRASKA", "NV": "NEVADA", "NH": "NEW HAMPSHIRE", "NJ": "NEW JERSEY",
            "NM": "NEW MEXICO", "NY": "NEW YORK", "NC": "NORTH CAROLINA", "ND": "NORTH DAKOTA", "OH": "OHIO",
            "OK": "OKLAHOMA", "OR": "OREGON", "PA": "PENNSYLVANIA", "RI": "RHODE ISLAND", "SC": "SOUTH CAROLINA",
            "SD": "SOUTH DAKOTA", "TN": "TENNESSEE", "TX": "TEXAS", "UT": "UTAH", "VT": "VERMONT",
            "VA": "VIRGINIA", "WA": "WASHINGTON", "WV": "WEST VIRGINIA", "WI": "WISCONSIN", "WY": "WYOMING"
        }
        
        allowed = set()
        for loc in self.locations:
            tokens = loc.strip().split()
            if tokens:
                last_token = tokens[-1].upper()
                if last_token in us_states_map:
                    allowed.add(last_token)
                    allowed.add(us_states_map[last_token])
                elif last_token in us_states_map.values():
                    allowed.add(last_token)
                    abbr = [k for k, v in us_states_map.items() if v == last_token][0]
                    allowed.add(abbr)
        return allowed

    @property
    def allowed_countries(self) -> Set[str]:
        """
        Returns the set of allowed countries for geographic validation.
        """
        return {"USA", "UNITED STATES", "UNITED STATES OF AMERICA", "US"}

    @classmethod
    def load(cls, cli_overrides: Optional[Dict[str, Any]] = None) -> "Config":
        """
        Loads, normalizes, and validates configurations from environment variables,
        with optional CLI overrides and default fallbacks.

        Args:
            cli_overrides: Optional dictionary of CLI configuration arguments.

        Returns:
            A fully validated Config instance.

        Raises:
            ValueError: If required configurations are missing or invalid.
        """
        load_dotenv()

        overrides = cli_overrides or {}

        # 1. Apify configurations
        apify_token = str(overrides.get("token") or os.getenv("APIFY_API_TOKEN", "")).strip()
        if not apify_token:
            raise ValueError("Apify API Token is missing. Please set APIFY_API_TOKEN in .env or pass --token.")

        apify_actor_id = str(overrides.get("actor_id") or os.getenv("APIFY_ACTOR_ID", "apify/google-maps-scraper")).strip()
        if not apify_actor_id:
            raise ValueError("Apify Actor ID cannot be empty.")

        # 2. Search parameters
        queries_raw = overrides.get("queries") or os.getenv("SEARCH_QUERIES")
        if queries_raw:
            if isinstance(queries_raw, list):
                search_queries = [str(q).strip() for q in queries_raw if str(q).strip()]
            else:
                search_queries = [q.strip() for q in str(queries_raw).split(",") if q.strip()]
        else:
            search_queries = DEFAULT_SEARCH_QUERIES

        if not search_queries:
            raise ValueError("Search queries list cannot be empty.")

        locations_raw = overrides.get("locations") or os.getenv("LOCATIONS")
        if locations_raw:
            if isinstance(locations_raw, list):
                locations = [str(l).strip() for l in locations_raw if str(l).strip()]
            else:
                locations = [l.strip() for l in str(locations_raw).split(",") if l.strip()]
        else:
            locations = DEFAULT_LOCATIONS

        if not locations:
            raise ValueError("Locations list cannot be empty.")

        # 3. Numeric parameters
        try:
            max_results_per_query = int(overrides.get("max_results") or os.getenv("MAX_RESULTS_PER_QUERY") or DEFAULT_MAX_RESULTS_PER_QUERY)
            if max_results_per_query <= 0:
                raise ValueError("max_results_per_query must be a positive integer.")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid max_results_per_query value: {e}")

        try:
            timeout_mins = int(overrides.get("timeout") or os.getenv("TIMEOUT_MINS") or DEFAULT_TIMEOUT_MINS)
            if timeout_mins <= 0:
                raise ValueError("timeout_mins must be a positive integer.")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid timeout_mins value: {e}")

        try:
            retry_count = int(overrides.get("retry_count") or os.getenv("RETRY_COUNT") or 3)
            if retry_count < 0:
                raise ValueError("retry_count must be zero or a positive integer.")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid retry_count value: {e}")

        try:
            min_similarity_score = int(overrides.get("min_similarity") or os.getenv("MIN_SIMILARITY_SCORE") or DEFAULT_MIN_SIMILARITY_SCORE)
            if not (0 <= min_similarity_score <= 100):
                raise ValueError("min_similarity_score must be between 0 and 100.")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid min_similarity_score value: {e}")

        # 4. System paths and constants
        log_level = str(overrides.get("log_level") or os.getenv("LOG_LEVEL", "INFO")).strip().upper()
        
        data_dir = Path(overrides.get("data_dir") or os.getenv("DATA_DIR") or DATA_DIR)
        raw_data_dir = Path(overrides.get("raw_data_dir") or os.getenv("RAW_DATA_DIR") or RAW_DATA_DIR)
        processed_data_dir = Path(overrides.get("processed_data_dir") or os.getenv("PROCESSED_DATA_DIR") or PROCESSED_DATA_DIR)
        output_data_dir = Path(overrides.get("output_data_dir") or os.getenv("OUTPUT_DATA_DIR") or OUTPUT_DATA_DIR)
        logs_dir = Path(overrides.get("logs_dir") or os.getenv("LOGS_DIR") or LOGS_DIR)

        cleaned_csv_name = str(overrides.get("cleaned_csv_name") or os.getenv("CLEANED_CSV_FILENAME") or CLEANED_CSV_FILENAME).strip()
        cleaned_xlsx_name = str(overrides.get("cleaned_xlsx_name") or os.getenv("CLEANED_XLSX_FILENAME") or CLEANED_XLSX_FILENAME).strip()
        clay_csv_name = str(overrides.get("clay_csv_name") or os.getenv("CLAY_CSV_FILENAME") or CLAY_CSV_FILENAME).strip()

        excel_theme_color = str(overrides.get("excel_theme_color") or os.getenv("EXCEL_THEME_COLOR", "1F4E79")).strip()

        return cls(
            apify_token=apify_token,
            apify_actor_id=apify_actor_id,
            search_queries=search_queries,
            locations=locations,
            max_results_per_query=max_results_per_query,
            timeout_mins=timeout_mins,
            retry_count=retry_count,
            log_level=log_level,
            data_dir=data_dir,
            raw_data_dir=raw_data_dir,
            processed_data_dir=processed_data_dir,
            output_data_dir=output_data_dir,
            logs_dir=logs_dir,
            cleaned_csv_name=cleaned_csv_name,
            cleaned_xlsx_name=cleaned_xlsx_name,
            clay_csv_name=clay_csv_name,
            min_similarity_score=min_similarity_score,
            excel_theme_color=excel_theme_color
        )
