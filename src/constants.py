from pathlib import Path
from typing import List, Set, Any

# Default directories and file paths
DATA_DIR = Path("data")
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "output"
LOGS_DIR = Path("logs")

# Output filenames
CLEANED_CSV_FILENAME = "cleaned.csv"
CLEANED_XLSX_FILENAME = "cleaned.xlsx"
CLAY_CSV_FILENAME = "clay_import.csv"

# Default search terms and locations
DEFAULT_SEARCH_QUERIES: List[str] = [
    "Real Estate Agency",
    "Real Estate Broker",
    "Residential Real Estate Agency",
    "Residential Real Estate Broker",
    "Real Estate Office",
    "Brokerage"
]

DEFAULT_LOCATIONS: List[str] = ["Miami FL"]

# Scraper configurations
DEFAULT_MAX_RESULTS_PER_QUERY = 50
DEFAULT_POLL_INTERVAL_SECS = 15
DEFAULT_TIMEOUT_MINS = 60

# Deduplication and filtering thresholds
DEFAULT_MIN_SIMILARITY_SCORE = 85
FUZZY_ADDRESS_MATCH_THRESHOLD = 80
FUZZY_NAME_MATCH_THRESHOLD = 85

# Filtering heuristics keywords
POSITIVE_KEYWORDS: Set[str] = {
    "residential", "brokerage", "broker", "realty", "real estate agency",
    "real estate agent", "realtor", "homes", "properties", "agency"
}

EXCLUDED_KEYWORDS: Set[str] = {
    "appraiser", "appraisal", "attorney", "lawyer", "legal", 
    "mortgage", "lender", "credit union", "developer", "builder",
    "construction", "title company", "home inspection", "surveyor",
    "commercial real estate agency", "commercial real estate broker"
}

# Standardized data model columns (exactly as defined in the specification)
STANDARDIZED_COLUMNS: List[str] = [
    "Business Name",
    "Category",
    "Website",
    "Phone",
    "Street",
    "City",
    "State",
    "Zip Code",
    "Country",
    "Rating",
    "Review Count",
    "Latitude",
    "Longitude",
    "Google Maps URL",
    "Google Place ID",
    "Business Email",
    "Owner Name",
    "Owner Title",
    "Owner Email",
    "Lead Score",
    "Lead Tier",
    "Score Breakdown",
    "Estimated Agent Count",
    "Office Count",
    "Years in Business",
    "LinkedIn URL",
    "Facebook URL",
    "Instagram URL",
    "YouTube URL",
    "X URL",
    "TikTok URL",
    "Has Blog",
    "Has Contact Form",
    "Has Property Search",
    "Has Mortgage Services",
    "Has Property Management",
    "Has Commercial Services",
    "Has Luxury Division",
    "Has Careers Page",
    "Has Multiple Offices",
    "Business Intelligence Confidence",
    "Estimated Transactions",
    "Estimated GCI",
    "Estimated Revenue Low",
    "Estimated Revenue High",
    "Revenue Confidence",
    "Revenue Reasoning",
    "Revenue Model Version",
    "Website Platform",
    "CMS",
    "IDX Provider",
    "CRM Platform",
    "Analytics Tools",
    "Marketing Tools",
    "Chat Provider",
    "Form Provider",
    "Consent Manager",
    "CDN Provider",
    "Technology Confidence",
    "Technology Reasoning",
    "Technology Model Version",
    "Decision Maker Name",
    "Decision Maker Title",
    "Decision Maker Confidence",
    "Decision Maker Status",
    "Verified Email",
    "Email Source",
    "Email Verified"
]

# Clay export columns (exactly as defined in the specification)
CLAY_COLUMNS: List[str] = [
    "Brokerage",
    "Website",
    "City",
    "State",
    "Phone",
    "Google Maps URL",
    "Lead Score",
    "Lead Tier",
    "Score Breakdown",
    "Estimated Agent Count",
    "Office Count",
    "Years in Business",
    "LinkedIn URL",
    "Facebook URL",
    "Instagram URL",
    "YouTube URL",
    "X URL",
    "TikTok URL",
    "Has Blog",
    "Has Contact Form",
    "Has Property Search",
    "Has Mortgage Services",
    "Has Property Management",
    "Has Commercial Services",
    "Has Luxury Division",
    "Has Careers Page",
    "Has Multiple Offices",
    "Business Intelligence Confidence",
    "Estimated Transactions",
    "Estimated GCI",
    "Estimated Revenue Low",
    "Estimated Revenue High",
    "Revenue Confidence",
    "Revenue Reasoning",
    "Revenue Model Version",
    "Website Platform",
    "CMS",
    "IDX Provider",
    "CRM Platform",
    "Analytics Tools",
    "Marketing Tools",
    "Chat Provider",
    "Form Provider",
    "Consent Manager",
    "CDN Provider",
    "Technology Confidence",
    "Technology Reasoning",
    "Technology Model Version",
    "Decision Maker Name",
    "Decision Maker Title",
    "Decision Maker Confidence",
    "Decision Maker Status",
    "Verified Email",
    "Email Source",
    "Email Verified"
]

# Lead Scoring Engine Configuration Rules
LEAD_SCORING_WEIGHTS: dict[str, int] = {
    "website_exists": 10,
    "business_email": 20,
    "owner_email": 25,
    "owner_detected": 10,
    "phone_exists": 5,
    "independent_brokerage": 10,
    "social_links_detected": 5,
    "no_website_penalty": -20,
    "generic_email_penalty": -10,
    "missing_phone_penalty": -5
}

LEAD_RATING_THRESHOLDS: list[dict[str, Any]] = [
    {"min": 4.8, "max": 5.0, "points": 15},
    {"min": 4.5, "max": 4.79, "points": 10},
    {"min": 4.0, "max": 4.49, "points": 5}
]

LEAD_REVIEW_THRESHOLDS: list[dict[str, Any]] = [
    {"min": 250, "max": 999999, "points": 20},
    {"min": 100, "max": 249, "points": 15},
    {"min": 50, "max": 99, "points": 10},
    {"min": 10, "max": 49, "points": 5}
]

FRANCHISE_NAMES: Set[str] = {
    "RE/MAX",
    "Keller Williams",
    "Coldwell Banker",
    "Century 21",
    "Compass",
    "Real Broker",
    "eXp Realty",
    "Berkshire Hathaway",
    "ERA",
    "Better Homes and Gardens",
    "Howard Hanna"
}

FREE_EMAIL_PROVIDERS: Set[str] = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "aol.com"
}

SOCIAL_PLATFORM_NAMES: Set[str] = {
    "facebook",
    "instagram",
    "linkedin",
    "twitter",
    "youtube",
    "pinterest",
    "tiktok"
}

LEAD_TIER_THRESHOLDS: list[dict[str, Any]] = [
    {"min": 90, "max": 100, "tier": "Platinum"},
    {"min": 75, "max": 89, "tier": "Gold"},
    {"min": 60, "max": 74, "tier": "Silver"},
    {"min": 40, "max": 59, "tier": "Bronze"},
    {"min": 0, "max": 39, "tier": "Low Priority"}
]

# Revenue Intelligence Engine Configuration Assumptions
REVENUE_MODEL_VERSION: str = "1.0.0"
AVERAGE_TRANSACTIONS_PER_AGENT: float = 10.0
AVERAGE_GCI_PER_TRANSACTION: float = 15000.0
AVERAGE_BROKERAGE_RETAINED_PERCENT: float = 0.20

# Multipliers for low/high range bounds
REVENUE_RANGE_MULTIPLIERS: dict[str, float] = {
    "low": 0.8,
    "high": 1.2
}

# Specializations average commission multipliers
REVENUE_SPECIALTY_MULTIPLIERS: dict[str, float] = {
    "luxury": 1.5,
    "commercial": 1.3,
    "property_management": 1.1
}

# Confidence Points System settings
REVENUE_CONFIDENCE_WEIGHTS: dict[str, int] = {
    "has_agent_count": 4,
    "has_office_count": 2,
    "has_years_in_business": 2,
    "bi_confidence_high": 3,
    "bi_confidence_medium": 1,
    "has_multiple_offices": 1
}

REVENUE_CONFIDENCE_THRESHOLDS: dict[str, int] = {
    "High": 9,
    "Medium": 5
}

# Technology Intelligence Engine Configuration
TECHNOLOGY_MODEL_VERSION: str = "1.0.0"

TECHNOLOGY_CONFIDENCE_THRESHOLDS: dict[str, int] = {
    "High": 2,
    "Medium": 1
}

TECH_SIGNATURES: dict[str, dict[str, Any]] = {
    # CMS Platforms
    "WordPress": {
        "category": "cms",
        "signatures": [
            "wp-content",
            "wp-includes",
            "wp-json",
            "wp-uploads",
            "generator\" content=\"WordPress"
        ]
    },
    "Wix": {
        "category": "cms",
        "signatures": [
            "wix.com",
            "wix-code",
            "_wix",
            "wixpress"
        ]
    },
    "Squarespace": {
        "category": "cms",
        "signatures": [
            "squarespace.com",
            "static1.squarespace.com",
            "squarespace-headers"
        ]
    },
    "Webflow": {
        "category": "cms",
        "signatures": [
            "webflow.css",
            "webflow.js",
            "generator\" content=\"Webflow",
            "data-wf-page"
        ]
    },
    "Joomla": {
        "category": "cms",
        "signatures": [
            "generator\" content=\"Joomla",
            "/media/system/js/",
            "option=com_"
        ]
    },
    "Drupal": {
        "category": "cms",
        "signatures": [
            "Drupal.settings",
            "Drupal.behaviors",
            "generator\" content=\"Drupal"
        ]
    },
    
    # IDX Providers
    "IDX Broker": {
        "category": "idx_provider",
        "signatures": [
            "idxbroker.com",
            "idx-broker",
            "idxbroker"
        ]
    },
    "Showcase IDX": {
        "category": "idx_provider",
        "signatures": [
            "showcaseidx.com",
            "showcase-idx",
            "sidx-"
        ]
    },
    "iHomefinder": {
        "category": "idx_provider",
        "signatures": [
            "ihomefinder.com",
            "ihomefinder",
            "ihf-"
        ]
    },
    "MLS Grid": {
        "category": "idx_provider",
        "signatures": [
            "mlsgrid.org",
            "mls grid",
            "mls-grid"
        ]
    },
    "IDX Home": {
        "category": "idx_provider",
        "signatures": [
            "idxhome.com",
            "idx home",
            "idx-home"
        ]
    },

    # CRM Platforms
    "BoomTown": {
        "category": "crm_platform",
        "signatures": [
            "boomtownre.com",
            "boomtown",
            "boomtown-"
        ]
    },
    "kvCORE": {
        "category": "crm_platform",
        "signatures": [
            "kvcore.com",
            "kvcore",
            "kv-core"
        ]
    },
    "Follow Up Boss": {
        "category": "crm_platform",
        "signatures": [
            "followupboss.com",
            "followupboss",
            "fub-"
        ]
    },
    "Real Geeks": {
        "category": "crm_platform",
        "signatures": [
            "realgeeks.com",
            "real geeks",
            "realgeeks"
        ]
    },
    "CINC": {
        "category": "crm_platform",
        "signatures": [
            "cinc.com",
            "commissionsinc.com",
            "cinc-"
        ]
    },
    "LionDesk": {
        "category": "crm_platform",
        "signatures": [
            "liondesk.com",
            "liondesk"
        ]
    },
    "Wise Agent": {
        "category": "crm_platform",
        "signatures": [
            "wiseagent.com",
            "wise agent",
            "wiseagent"
        ]
    },

    # Analytics Tools
    "Google Analytics": {
        "category": "analytics_tools",
        "signatures": [
            "google-analytics.com",
            "ga.js",
            "analytics.js",
            "gtag("
        ]
    },
    "Google Tag Manager": {
        "category": "analytics_tools",
        "signatures": [
            "googletagmanager.com",
            "gtm.js",
            "gtm.js?id="
        ]
    },
    "Microsoft Clarity": {
        "category": "analytics_tools",
        "signatures": [
            "clarity.ms",
            "clarity-js",
            "c.queue.push"
        ]
    },
    "Meta Pixel": {
        "category": "analytics_tools",
        "signatures": [
            "connect.facebook.net",
            "fbevents.js",
            "fbq("
        ]
    },
    "Hotjar": {
        "category": "analytics_tools",
        "signatures": [
            "static.hotjar.com",
            "hj.q=hj.q",
            "hj("
        ]
    },

    # Chat Providers
    "Intercom": {
        "category": "chat_provider",
        "signatures": [
            "widget.intercom.io",
            "intercomSettings",
            "Intercom("
        ]
    },
    "Drift": {
        "category": "chat_provider",
        "signatures": [
            "drift.com",
            "drift.js",
            "drift("
        ]
    },
    "HubSpot Chat": {
        "category": "chat_provider",
        "signatures": [
            "js.hs-leadflows.com",
            "hs-messages-iframe",
            "HubSpotConversations"
        ]
    },
    "Tidio": {
        "category": "chat_provider",
        "signatures": [
            "code.tidio.co",
            "tidioChat",
            "tidio-"
        ]
    },
    "Zendesk": {
        "category": "chat_provider",
        "signatures": [
            "zopim.com",
            "zendesk.com/embeddable",
            "zEmbed"
        ]
    },

    # Form Providers
    "Gravity Forms": {
        "category": "form_provider",
        "signatures": [
            "gforms_",
            "gravityforms",
            "gf_placeholder"
        ]
    },
    "Contact Form 7": {
        "category": "form_provider",
        "signatures": [
            "wpcf7-",
            "contact-form-7",
            "cf7-"
        ]
    },
    "HubSpot Forms": {
        "category": "form_provider",
        "signatures": [
            "forms.hsforms.com",
            "hbspt.forms",
            "hs-form"
        ]
    },
    "Typeform": {
        "category": "form_provider",
        "signatures": [
            "typeform.com/embed",
            "data-tf-",
            "typeform-widget"
        ]
    },
    "JotForm": {
        "category": "form_provider",
        "signatures": [
            "jotform.com",
            "jotform-form",
            "jotform"
        ]
    },

    # Consent Managers
    "Cookiebot": {
        "category": "consent_manager",
        "signatures": [
            "cookiebot.com",
            "Cookiebot",
            "data-cbid="
        ]
    },
    "OneTrust": {
        "category": "consent_manager",
        "signatures": [
            "onetrust.com",
            "otSDKLoader.js",
            "ot-cookie-settings"
        ]
    },
    "Termly": {
        "category": "consent_manager",
        "signatures": [
            "termly.io",
            "termly-embed",
            "termly-"
        ]
    },

    # CDN Providers
    "Cloudflare": {
        "category": "cdn_provider",
        "signatures": [
            "cloudflare.com",
            "/cdn-cgi/",
            "cloudflare-static"
        ]
    },
    "CloudFront": {
        "category": "cdn_provider",
        "signatures": [
            "cloudfront.net",
            "cloudfront.net/"
        ]
    },
    "Fastly": {
        "category": "cdn_provider",
        "signatures": [
            "fastly.net",
            "fastly-analytics"
        ]
    },

    # Marketing Automation
    "HubSpot": {
        "category": "marketing_tools",
        "signatures": [
            "hubspot.com",
            "hs-scripts.com",
            "js.hs-scripts.com"
        ]
    },
    "Mailchimp": {
        "category": "marketing_tools",
        "signatures": [
            "chimpstatic.com",
            "mailchimp.com",
            "mc-embed"
        ]
    },
    "ActiveCampaign": {
        "category": "marketing_tools",
        "signatures": [
            "activecampaign.com",
            "ac-track",
            "trackcmp"
        ]
    }
}

