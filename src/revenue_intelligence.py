from dataclasses import replace
from typing import List, Optional

from src.models import Lead
from src import constants
from src.logger import get_logger

logger = get_logger("revenue_intelligence")


class RevenueIntelligence:
    """
    Estimates annual brokerage transactions, gross commission income (GCI),
    and brokerage retained revenue range based exclusively on observed lead signals.
    """

    def __init__(self) -> None:
        self.model_version = constants.REVENUE_MODEL_VERSION
        self.transactions_per_agent = constants.AVERAGE_TRANSACTIONS_PER_AGENT
        self.gci_per_transaction = constants.AVERAGE_GCI_PER_TRANSACTION
        self.retained_percent = constants.AVERAGE_BROKERAGE_RETAINED_PERCENT
        self.range_multipliers = constants.REVENUE_RANGE_MULTIPLIERS
        self.specialty_multipliers = constants.REVENUE_SPECIALTY_MULTIPLIERS
        self.confidence_weights = constants.REVENUE_CONFIDENCE_WEIGHTS
        self.confidence_thresholds = constants.REVENUE_CONFIDENCE_THRESHOLDS

    def estimate_leads(self, leads: List[Lead]) -> List[Lead]:
        """
        Calculates revenue details for a list of Lead objects, returning new copies.
        """
        logger.info(f"Estimating revenue metrics for {len(leads)} leads...")
        estimated_leads: List[Lead] = []

        for lead in leads:
            try:
                est = self.estimate_lead(lead)
                estimated_leads.append(est)
            except Exception as e:
                logger.error(f"Failed to estimate revenue for lead {lead.business_name}: {e}")
                estimated_leads.append(lead)

        logger.info("Revenue estimation processing complete.")
        return estimated_leads

    def estimate_lead(self, lead: Lead) -> Lead:
        """
        Computes transactions, GCI, revenue range, confidence level, and reasoning
        for a single Lead.
        """
        reasoning: List[str] = []

        # If agent count is missing, we cannot estimate transactions or revenue.
        # "Never guess without evidence... If exact counts cannot be determined: return None."
        if lead.estimated_agent_count is None:
            reasoning.append("Unable to estimate revenue: missing agent count")
            return replace(
                lead,
                estimated_transactions=None,
                estimated_gci=None,
                estimated_revenue_low=None,
                estimated_revenue_high=None,
                revenue_confidence="Low",
                revenue_reasoning=reasoning,
                revenue_model_version=self.model_version
            )

        # 1. Estimate Transactions
        agents = lead.estimated_agent_count
        tx_per_agent = self.transactions_per_agent
        estimated_tx = int(agents * tx_per_agent)
        
        reasoning.append(f"Estimated {agents} active agents")
        reasoning.append(f"Average {tx_per_agent} transactions per agent")

        # 2. Estimate GCI per Transaction with Specialty Multipliers
        gci_multiplier = 1.0
        if lead.has_luxury_division:
            mult = self.specialty_multipliers.get("luxury", 1.5)
            gci_multiplier *= mult
            reasoning.append(f"Luxury division detected (GCI multiplier x{mult})")
            
        if lead.has_commercial_services:
            mult = self.specialty_multipliers.get("commercial", 1.3)
            gci_multiplier *= mult
            reasoning.append(f"Commercial services detected (GCI multiplier x{mult})")

        if lead.has_property_management:
            mult = self.specialty_multipliers.get("property_management", 1.1)
            gci_multiplier *= mult
            reasoning.append(f"Property management services detected (GCI multiplier x{mult})")

        gci_per_tx = self.gci_per_transaction * gci_multiplier
        estimated_gci = estimated_tx * gci_per_tx

        # 3. Estimate Brokerage Retained Revenue Range
        base_retained_rev = estimated_gci * self.retained_percent
        low_mult = self.range_multipliers.get("low", 0.8)
        high_mult = self.range_multipliers.get("high", 1.2)
        
        rev_low = base_retained_rev * low_mult
        rev_high = base_retained_rev * high_mult

        reasoning.append(f"Brokerage retained rate: {int(self.retained_percent * 100)}%")

        # 4. Compute Confidence Score
        points = 0
        if lead.estimated_agent_count is not None:
            points += self.confidence_weights.get("has_agent_count", 4)
        if lead.office_count is not None:
            points += self.confidence_weights.get("has_office_count", 2)
        if lead.years_in_business is not None:
            points += self.confidence_weights.get("has_years_in_business", 2)
        if lead.has_multiple_offices:
            points += self.confidence_weights.get("has_multiple_offices", 1)

        bi_conf = lead.business_intelligence_confidence
        if bi_conf == "High":
            points += self.confidence_weights.get("bi_confidence_high", 3)
        elif bi_conf == "Medium":
            points += self.confidence_weights.get("bi_confidence_medium", 1)

        # Decide confidence tier based on thresholds
        high_threshold = self.confidence_thresholds.get("High", 9)
        med_threshold = self.confidence_thresholds.get("Medium", 5)

        if points >= high_threshold:
            confidence = "High"
        elif points >= med_threshold:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Explain confidence in reasoning
        reasoning.append(f"Confidence score: {points} points (BI confidence: {bi_conf})")

        return replace(
            lead,
            estimated_transactions=estimated_tx,
            estimated_gci=estimated_gci,
            estimated_revenue_low=rev_low,
            estimated_revenue_high=rev_high,
            revenue_confidence=confidence,
            revenue_reasoning=reasoning,
            revenue_model_version=self.model_version
        )
