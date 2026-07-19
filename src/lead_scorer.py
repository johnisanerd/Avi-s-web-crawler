import re
from dataclasses import replace
from typing import List, Optional

from src.models import Lead
from src import constants
from src.logger import get_logger

logger = get_logger("lead_scorer")


class LeadScorer:
    """
    Evaluates enriched Lead records and computes a sales opportunity score,
    matching tier, and detailed scoring breakdown according to configurable rules.
    """

    def __init__(self) -> None:
        # Load configurable weights and business rules from constants.py
        self.weights = constants.LEAD_SCORING_WEIGHTS
        self.rating_thresholds = constants.LEAD_RATING_THRESHOLDS
        self.review_thresholds = constants.LEAD_REVIEW_THRESHOLDS
        self.franchise_names = constants.FRANCHISE_NAMES
        self.free_email_providers = constants.FREE_EMAIL_PROVIDERS
        self.social_platforms = constants.SOCIAL_PLATFORM_NAMES
        self.tier_thresholds = constants.LEAD_TIER_THRESHOLDS

    def score_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Orchestrates scoring for a collection of Lead objects, returning new scored copies.
        """
        logger.info(f"Computing sales opportunity scores for {len(leads)} leads...")
        scored_leads: List[Lead] = []

        for lead in leads:
            try:
                scored = self.score_lead(lead)
                scored_leads.append(scored)
            except Exception as e:
                logger.error(f"Failed to score lead {lead.business_name}: {e}")
                scored_leads.append(lead)

        logger.info("Lead scoring calculations complete.")
        return scored_leads

    def score_lead(self, lead: Lead) -> Lead:
        """
        Calculates the score, tier, and breakdown for a single Lead record.
        """
        score = 0
        breakdown: List[str] = []

        # 1. Website Checks
        if lead.website:
            val = self.weights.get("website_exists", 10)
            score += val
            breakdown.append(f"Website exists (+{val})")
        else:
            val = self.weights.get("no_website_penalty", -20)
            score += val
            breakdown.append(f"No website ({val})")

        # 2. Contact/Email Checks
        if lead.business_email:
            val = self.weights.get("business_email", 20)
            score += val
            breakdown.append(f"Business email (+{val})")

            # Generic Email check
            domain = lead.business_email.split('@')[-1].lower().strip()
            if domain in self.free_email_providers:
                penalty = self.weights.get("generic_email_penalty", -10)
                score += penalty
                breakdown.append(f"Generic business email ({penalty})")

        if lead.owner_email:
            val = self.weights.get("owner_email", 25)
            score += val
            breakdown.append(f"Owner email (+{val})")

        if lead.owner_name:
            val = self.weights.get("owner_detected", 10)
            score += val
            breakdown.append(f"Owner detected (+{val})")

        # 3. Phone Checks
        if lead.phone:
            val = self.weights.get("phone_exists", 5)
            score += val
            breakdown.append(f"Phone exists (+{val})")
        else:
            val = self.weights.get("missing_phone_penalty", -5)
            score += val
            breakdown.append(f"Missing phone ({val})")

        # 4. Google Rating Checks
        rating_points = 0
        rating_matched = False
        for rule in self.rating_thresholds:
            min_r = rule.get("min", 0.0)
            max_r = rule.get("max", 5.0)
            if min_r <= lead.rating <= max_r:
                rating_points = rule.get("points", 0)
                rating_matched = True
                break
        if rating_matched and rating_points > 0:
            score += rating_points
            breakdown.append(f"Rating {lead.rating} (+{rating_points})")
        else:
            breakdown.append(f"Rating {lead.rating} (+0)")

        # 5. Review Count Checks
        review_points = 0
        review_matched = False
        for rule in self.review_thresholds:
            min_rev = rule.get("min", 0)
            max_rev = rule.get("max", 999999)
            if min_rev <= lead.review_count <= max_rev:
                review_points = rule.get("points", 0)
                review_matched = True
                break
        if review_matched and review_points > 0:
            score += review_points
            breakdown.append(f"{lead.review_count} Google reviews (+{review_points})")
        else:
            breakdown.append(f"{lead.review_count} Google reviews (+0)")

        # 6. Franchise vs Independent Check
        is_franchise = False
        for f_name in self.franchise_names:
            pattern = r'(?:\b|(?<=\W))' + re.escape(f_name) + r'(?:\b|(?=\W))'
            if re.search(pattern, lead.business_name, re.IGNORECASE):
                is_franchise = True
                break

        if is_franchise:
            # National franchise gets 0 additional points
            breakdown.append("National franchise (+0)")
        else:
            val = self.weights.get("independent_brokerage", 10)
            score += val
            breakdown.append(f"Independent brokerage (+{val})")

        # 7. Social Links Check
        has_social = False
        if lead.social_profiles:
            for platform in self.social_platforms:
                if lead.social_profiles.get(platform):
                    has_social = True
                    break
        if has_social:
            val = self.weights.get("social_links_detected", 5)
            score += val
            breakdown.append(f"Social links detected (+{val})")

        # Clamp final score to [0, 100]
        clamped_score = max(0, min(100, score))

        # 8. Tier Thresholds Match
        lead_tier = "Low Priority"
        for tier_rule in self.tier_thresholds:
            min_score = tier_rule.get("min", 0)
            max_score = tier_rule.get("max", 100)
            if min_score <= clamped_score <= max_score:
                lead_tier = tier_rule.get("tier", "Low Priority")
                break

        return replace(
            lead,
            lead_score=clamped_score,
            lead_tier=lead_tier,
            score_breakdown=breakdown
        )
