"""
Externalized configuration constants for Decision Maker Intelligence.
Contains configurable weights, title mappings, ignored titles, confidence thresholds,
and generic email lists. This keeps business rules decoupled from extraction logic.
"""

from typing import Dict, Set

# Configuration version for cache invalidation
CONFIG_VERSION: str = "1.1.0"

# Page priority weights (higher score = higher priority page type)
PAGE_WEIGHTS: Dict[str, float] = {
    "about": 100.0,
    "team": 90.0,
    "leadership": 85.0,
    "our-story": 80.0,
    "contact": 70.0,
    "homepage": 60.0,
    "footer": 40.0,
    "general": 50.0
}

# Leadership title weights (higher score = higher authority/decision maker priority)
LEADERSHIP_TITLES: Dict[str, float] = {
    "owner": 100.0,
    "founder": 100.0,
    "broker/owner": 100.0,
    "owner/broker": 100.0,
    "managing partner": 95.0,
    "principal broker": 90.0,
    "managing broker": 90.0,
    "ceo": 85.0,
    "president": 85.0,
    "chief executive officer": 85.0,
}

# Titles to strictly ignore (non-leadership / individual contributor roles)
IGNORED_TITLES: Set[str] = {
    "agent",
    "realtor",
    "staff",
    "assistant",
    "transaction coordinator",
    "office administrator",
    "administrative assistant",
    "receptionist",
    "sales associate",
    "associate",
    "real estate agent",
    "property manager",
    "leasing agent",
    "intern"
}

# Terms that MUST NOT appear in a valid human name candidate
FORBIDDEN_NAME_PATTERNS: Set[str] = {
    "mls", "idx", "copyright", "privacy", "cookie", "terms", "request", "search",
    "login", "admin", "support", "street", "avenue", "road", "blvd", "suite", "drive",
    "court", "way", "phone", "tel", "fax", "zip", "zipcode", "menu", "navigation",
    "home", "contact", "about", "services", "real", "estate", "realty", "group",
    "company", "properties", "llc", "inc", "corp", "corporation", "office", "brokerage",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut",
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire",
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming"
}

# Positive and negative scoring delta weights
SCORING_WEIGHTS: Dict[str, float] = {
    "title_base_multiplier": 0.40,
    "page_base_multiplier": 0.20,
    "email_direct_linked": 30.0,
    "email_mailto_linked": 25.0,
    "email_pattern_matched": 20.0,
    "social_confirmation": 15.0,
    "repeated_appearance": 10.0,
    "dual_title_combo_bonus": 10.0,
    "footer_only_penalty": -25.0,
    "single_appearance_penalty": -10.0,
    "weak_name_format_penalty": -15.0,
    "conflicting_title_penalty": -20.0,
    "no_email_penalty": -15.0
}

# Minimum confidence threshold (0-100). If score < threshold, status is NO_DECISION_MAKER.
MIN_CONFIDENCE_THRESHOLD: int = 40

# Generic email prefixes that MUST NEVER be assigned to an individual
GENERIC_EMAIL_PREFIXES: Set[str] = {
    "info",
    "office",
    "hello",
    "contact",
    "support",
    "admin",
    "legal",
    "privacy",
    "dmca",
    "help",
    "sales",
    "billing",
    "careers",
    "jobs",
    "inquiries",
    "general",
    "team",
    "mail"
}

# Cache directory setting
DEFAULT_CACHE_DIR: str = "cache/decision_maker"
