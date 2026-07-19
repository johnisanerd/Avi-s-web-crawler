from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from src.models import RawLead, Lead
from src.mappers import raw_lead_to_lead
from src.normalize import normalize_lead
from src.validators import validate_lead
from src.filters import check_residential_lead
from src.dedupe import deduplicate_leads


@dataclass(slots=True)
class ProcessingResult:
    """
    Structured outcome of the processing pipeline stage.
    """
    leads: List[Lead]
    validation_failures_count: int
    filtered_count: int
    duplicate_count: int
    stats: Dict[str, Any]


def process_leads(
    raw_leads: List[RawLead],
    min_similarity_score: int = 85,
    allowed_states: Optional[Set[str]] = None,
    allowed_countries: Optional[Set[str]] = None
) -> ProcessingResult:
    """
    Orchestrates the translation, validation, normalization, filtering, and
    deduplication of leads.

    Args:
        raw_leads: List of raw leads scraped from Apify.
        min_similarity_score: Similarity threshold for deduplication.
        allowed_states: Optional set of allowed US states.
        allowed_countries: Optional set of allowed countries.

    Returns:
        ProcessingResult containing the final unique leads and step execution statistics.
    """
    validation_failures = 0
    filtered_count = 0
    valid_leads: List[Lead] = []

    for raw in raw_leads:
        # 1. Translate RawLead -> Lead representation
        lead = raw_lead_to_lead(raw)

        # 2. Validate standard lead fields
        if not validate_lead(lead):
            validation_failures += 1
            continue

        # 3. Apply normalization rules
        normalized = normalize_lead(lead)

        # 4. Filter based on residential real estate heuristics and geographic region
        filter_res = check_residential_lead(
            normalized,
            allowed_states=allowed_states,
            allowed_countries=allowed_countries
        )
        if not filter_res.accepted:
            filtered_count += 1
            continue

        valid_leads.append(normalized)

    # 5. Deduplicate verified residential leads
    deduplicated = deduplicate_leads(valid_leads, min_similarity_score)
    duplicate_count = len(valid_leads) - len(deduplicated)

    stats = {
        "raw_input_count": len(raw_leads),
        "validation_failures": validation_failures,
        "filtered_out": filtered_count,
        "duplicates_removed": duplicate_count,
        "final_output_count": len(deduplicated)
    }

    return ProcessingResult(
        leads=deduplicated,
        validation_failures_count=validation_failures,
        filtered_count=filtered_count,
        duplicate_count=duplicate_count,
        stats=stats
    )
