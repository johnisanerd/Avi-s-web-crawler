from dataclasses import replace
from typing import List, Dict, Set
from rapidfuzz import fuzz
from src.models import Lead
from src.constants import FUZZY_ADDRESS_MATCH_THRESHOLD, FUZZY_NAME_MATCH_THRESHOLD


def _get_richness_score(lead: Lead) -> float:
    """
    Calculates a richness score to prioritize leads during merging.
    Internal helper, deterministic and side-effect free.
    """
    score = 0.0
    if lead.website:
        score += 5.0
    if lead.phone:
        score += 3.0
    if lead.street or lead.city or lead.state or lead.zip_code:
        score += 2.0
    
    score += min(lead.review_count / 10.0, 5.0)
    
    if lead.rating:
        score += lead.rating
        
    return score


def deduplicate_leads(leads: List[Lead], min_similarity_score: int = 85) -> List[Lead]:
    """
    Deduplicates a list of Lead objects based on a priority hierarchy:
    1. Google Place ID (exact match on non-empty value)
    2. Website (exact match on non-empty website)
    3. Address (fuzzy comparison via RapidFuzz)
    4. Business Name (fuzzy comparison inside matching City/State/ZIP)

    When duplicates are identified, preserves the Lead record with the highest
    richness score and merges their source queries. Does not mutate inputs.

    Args:
        leads: A list of input Lead records.
        min_similarity_score: Minimum fuzzy similarity score (0-100).

    Returns:
        A new list of deduplicated Lead records.
    """
    if not leads:
        return []

    # Sort input copy by richness score descending so we keep the most complete record
    sorted_leads = sorted(leads, key=_get_richness_score, reverse=True)

    unique_leads: List[Lead] = []
    
    # Efficient lookup indexes
    place_id_map: Dict[str, Lead] = {}
    website_map: Dict[str, Lead] = {}
    
    # Buckets to localize fuzzy comparisons geographically (ZIP or City/State)
    geo_buckets: Dict[str, List[Lead]] = {}

    for lead in sorted_leads:
        duplicate_of: Lead = None

        # 1. Google Place ID exact match
        if lead.google_place_id:
            if lead.google_place_id in place_id_map:
                duplicate_of = place_id_map[lead.google_place_id]

        # 2. Website exact match
        if not duplicate_of and lead.website:
            if lead.website in website_map:
                duplicate_of = website_map[lead.website]

        # Determine geographic bucket key
        geo_key = ""
        if lead.zip_code:
            geo_key = f"zip_{lead.zip_code.lower()}"
        elif lead.city and lead.state:
            geo_key = f"loc_{lead.city.lower()}_{lead.state.lower()}"

        # Geographically localized fuzzy matching candidates
        candidates = geo_buckets.get(geo_key, []) if geo_key else []

        # 3. Address fuzzy match
        if not duplicate_of and lead.street and geo_key:
            for candidate in candidates:
                if candidate.street:
                    score = fuzz.token_sort_ratio(lead.street.lower(), candidate.street.lower())
                    if score >= FUZZY_ADDRESS_MATCH_THRESHOLD:
                        duplicate_of = candidate
                        break

        # 4. Name fuzzy match (within same location bucket)
        if not duplicate_of and lead.business_name and geo_key:
            for candidate in candidates:
                score = fuzz.token_sort_ratio(lead.business_name.lower(), candidate.business_name.lower())
                # Require higher score for name matching
                if score >= max(min_similarity_score, FUZZY_NAME_MATCH_THRESHOLD):
                    duplicate_of = candidate
                    break

        if duplicate_of:
            # Construct a new merged Lead instance to avoid mutating the original
            merged_queries = duplicate_of.source_queries | lead.source_queries
            merged_lead = replace(duplicate_of, source_queries=merged_queries)
            
            # Replace duplicate_of in unique list
            idx = unique_leads.index(duplicate_of)
            unique_leads[idx] = merged_lead
            
            # Update indexes to point to the new merged Lead
            if merged_lead.google_place_id:
                place_id_map[merged_lead.google_place_id] = merged_lead
            if merged_lead.website:
                website_map[merged_lead.website] = merged_lead
            
            # Resolve and update duplicate_of in its original geo bucket if present
            dup_geo_key = ""
            if duplicate_of.zip_code:
                dup_geo_key = f"zip_{duplicate_of.zip_code.lower()}"
            elif duplicate_of.city and duplicate_of.state:
                dup_geo_key = f"loc_{duplicate_of.city.lower()}_{duplicate_of.state.lower()}"

            if dup_geo_key and dup_geo_key in geo_buckets:
                geo_list = geo_buckets[dup_geo_key]
                if duplicate_of in geo_list:
                    geo_idx = geo_list.index(duplicate_of)
                    geo_list[geo_idx] = merged_lead
        else:
            # Create a clean copy to populate unique set
            new_lead = replace(lead, source_queries=set(lead.source_queries))
            unique_leads.append(new_lead)
            
            # Index new lead
            if new_lead.google_place_id:
                place_id_map[new_lead.google_place_id] = new_lead
            if new_lead.website:
                website_map[new_lead.website] = new_lead
                
            if geo_key:
                if geo_key not in geo_buckets:
                    geo_buckets[geo_key] = []
                geo_buckets[geo_key].append(new_lead)

    return unique_leads
