"""
Decision Maker Intelligence Module

Developer Documentation:
------------------------
1. Candidate Extraction:
   Inspects PageBlock objects derived from pre-normalized HTML pages. Uses precompiled regex
   to extract all candidate names paired with leadership titles (Owner, Founder, Principal Broker, etc.).
   Collects candidates across all pages without stopping early.

2. Candidate Validation:
   Filters out ignored non-leadership titles (Agent, Staff, Assistant, etc.) and validates human names
   against FORBIDDEN_NAME_PATTERNS (rejecting MLS, IDX, Copyright, Address terms, phone digits, etc.).

3. Candidate Merging:
   Duplicates discovered across multiple pages are merged into single DecisionMakerCandidate objects
   with unified evidence logs prior to scoring.

4. Scoring Engine & Breakdown:
   Evaluates title base weight, page priority weight, direct/pattern email matches, social profile
   confirmations, appearance counts, and penalties (footer-only, single appearance, no email).
   Stores explicit scoring_breakdown dictionary for transparency.

5. Email Verification & Traceability:
   Checks 5 deterministic matching strategies (FIRST_DOT_LAST, EXACT_FULL_NAME, FIRST_INITIAL_LAST,
   FIRST_NAME, LAST_NAME), strictly excluding generic inboxes (info@, office@, etc.).
   Records exact strategy trace.

6. Conflict Resolution & Threshold Enforceability:
   Detects competing high-confidence candidates and logs conflict details.
   Enforces MIN_CONFIDENCE_THRESHOLD (40). Winners below threshold yield status="NO_DECISION_MAKER".

7. Content-Hashed Cache Invalidation:
   Derives a SHA-256 hash from HTML pages, URLs, social profile URLs, and CONFIG_VERSION.
   Automatically invalidates cache if page content or configuration changes.

8. Fail-Safe Exception Handling & Diagnostics:
   Executes safely without halting pipeline on unexpected inputs. Records processing_time_ms per
   company and diagnostic metrics (hits, misses, invalidations, average confidence, processing speeds).
"""

import json
import re
import time
import hashlib
from pathlib import Path
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from src.models import (
    Lead,
    PageBlock,
    DecisionMakerEvidence,
    DecisionMakerCandidate,
    DecisionMaker,
    WebsiteSnapshot
)
from src.decision_maker_config import (
    CONFIG_VERSION,
    PAGE_WEIGHTS,
    LEADERSHIP_TITLES,
    IGNORED_TITLES,
    FORBIDDEN_NAME_PATTERNS,
    SCORING_WEIGHTS,
    MIN_CONFIDENCE_THRESHOLD,
    GENERIC_EMAIL_PREFIXES,
    DEFAULT_CACHE_DIR
)
from src.email_utils import (
    normalize_email,
    email_matches_domain,
    is_generic_email,
    is_personal_email,
    match_email_to_name
)
from src.html_parser import parse_html_to_blocks
from src.logger import get_logger

logger = get_logger("decision_maker_intelligence")


class DecisionMakerIntelligence:
    """
    Production-grade Decision Maker Intelligence engine.
    Fully deterministic, cache-aware, fail-safe, and decoupled.
    """

    def __init__(self, cache_dir: Optional[Path] = None, debug_mode: bool = False) -> None:
        self.cache_dir = cache_dir or Path(DEFAULT_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.debug_mode = debug_mode
        
        # Precompile regex patterns for performance
        self.name_title_regex = re.compile(r'^[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}$')
        self.mailto_regex = re.compile(r'href=["\']mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']', re.IGNORECASE)
        self.raw_email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # Module diagnostic statistics metrics
        self.stats = {
            "companies_processed": 0,
            "candidates_extracted": 0,
            "candidates_validated": 0,
            "verified_emails": 0,
            "generic_emails_rejected": 0,
            "social_confirmations": 0,
            "no_decision_maker": 0,
            "total_confidence": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_invalidations": 0,
            "total_processing_time_ms": 0.0,
            "fastest_time_ms": float("inf"),
            "slowest_time_ms": 0.0
        }

    def analyze_leads(self, leads: List[Lead], domain_cache: Dict[str, Any]) -> List[Lead]:
        """
        Orchestrates Decision Maker Intelligence analysis over Lead records safely.
        Fail-safe: unexpected errors in a lead return status="NO_DECISION_MAKER" without crashing pipeline.
        """
        logger.info(f"Running Decision Maker Intelligence on {len(leads)} leads...")
        updated_leads: List[Lead] = []

        for lead in leads:
            start_t = time.perf_counter()
            try:
                snapshot = self._build_website_snapshot(lead, domain_cache)
                decision_maker = self.analyze_snapshot(snapshot)
                
                duration_ms = (time.perf_counter() - start_t) * 1000.0
                decision_maker.processing_time_ms = round(duration_ms, 2)
                self._update_timing_stats(duration_ms)

                updated_lead = self._update_lead_with_decision_maker(lead, decision_maker)
                updated_leads.append(updated_lead)
            except Exception as e:
                duration_ms = (time.perf_counter() - start_t) * 1000.0
                logger.error(f"Fail-safe caught exception for lead {lead.business_name}: {e}", exc_info=True)
                fallback_dm = DecisionMaker(
                    status="NO_DECISION_MAKER",
                    processing_time_ms=round(duration_ms, 2)
                )
                updated_leads.append(self._update_lead_with_decision_maker(lead, fallback_dm))

        logger.info(f"Decision Maker Intelligence completed. Diagnostics: {self.get_statistics()}")
        return updated_leads

    def analyze_snapshot(self, snapshot: WebsiteSnapshot) -> DecisionMaker:
        """
        Processes a single WebsiteSnapshot and returns a structured DecisionMaker object.
        Uses content hashing for deterministic cache invalidation.
        """
        self.stats["companies_processed"] += 1
        domain = snapshot.domain or "unknown"

        # Compute content hash incorporating pages, URLs, social profiles, and CONFIG_VERSION
        content_hash = self._compute_content_hash(snapshot)

        # Check content-hashed cache
        cached_res = self._read_hashed_cache(domain, content_hash)
        if cached_res:
            self.stats["cache_hits"] += 1
            self.stats["total_confidence"] += cached_res.confidence_score
            return cached_res

        self.stats["cache_misses"] += 1

        # 1. Parse HTML pages into PageBlocks
        page_blocks: List[PageBlock] = []
        for url, html in snapshot.pages.items():
            blocks = parse_html_to_blocks(url, html)
            page_blocks.extend(blocks)

        # Stage 1: Extract ALL candidates
        extracted_candidates = self.extract_candidates(page_blocks)
        self.stats["candidates_extracted"] += len(extracted_candidates)

        # Stage 2: Validate candidates
        validated_candidates = self.validate_candidates(extracted_candidates)
        self.stats["candidates_validated"] += len(validated_candidates)

        # Stage 3: Merge candidate sightings across pages
        merged_candidates = self.merge_candidates(validated_candidates)

        # Stage 4: Score candidates with positive & negative evidence
        scored_candidates = self.score_candidates(merged_candidates, snapshot)

        # Stage 5: Conflict detection
        conflicts = self.detect_conflicts(scored_candidates)

        # Stage 6: Select winner and verify email
        decision_maker = self.select_winner(scored_candidates, conflicts, snapshot)

        # Write content-hashed cache
        self.stats["total_confidence"] += decision_maker.confidence_score
        self._write_hashed_cache(domain, content_hash, decision_maker)

        return decision_maker

    def extract_candidates(self, page_blocks: List[PageBlock]) -> List[DecisionMakerCandidate]:
        """
        Stage 1: Extract ALL potential leadership candidates across all PageBlock objects.
        Never stops at the first match.
        """
        candidates: List[DecisionMakerCandidate] = []

        for block in page_blocks:
            lines = [line.strip() for line in block.text.split('\n') if line.strip()]

            for i, line in enumerate(lines):
                line_lower = line.lower()

                for title_key, base_weight in LEADERSHIP_TITLES.items():
                    pattern1 = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\b\s*(?:,|\s*-\s*|\s*\|\s*|\s*&\s*)\s*(?:[^\n,]*\b)?' + re.escape(title_key) + r'\b'
                    pattern2 = r'\b' + re.escape(title_key) + r'\b\s*(?::|\s*-\s*|\s*\|\s*)?\s*\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\b'

                    m1 = re.search(pattern1, line, re.IGNORECASE)
                    if m1:
                        cand_name = m1.group(1).strip()
                        candidates.append(DecisionMakerCandidate(
                            name=cand_name,
                            title=title_key.title(),
                            page_url=block.page_url,
                            page_type=block.page_type,
                            snippet=line,
                            title_weight=base_weight,
                            page_weight=PAGE_WEIGHTS.get(block.page_type, 50.0)
                        ))

                    m2 = re.search(pattern2, line, re.IGNORECASE)
                    if m2 and not m1:
                        cand_name = m2.group(1).strip()
                        candidates.append(DecisionMakerCandidate(
                            name=cand_name,
                            title=title_key.title(),
                            page_url=block.page_url,
                            page_type=block.page_type,
                            snippet=line,
                            title_weight=base_weight,
                            page_weight=PAGE_WEIGHTS.get(block.page_type, 50.0)
                        ))

                    if title_key in line_lower and not m1 and not m2:
                        if i > 0 and self.name_title_regex.match(lines[i - 1]):
                            candidates.append(DecisionMakerCandidate(
                                name=lines[i - 1],
                                title=title_key.title(),
                                page_url=block.page_url,
                                page_type=block.page_type,
                                snippet=f"{lines[i-1]} | {line}",
                                title_weight=base_weight,
                                page_weight=PAGE_WEIGHTS.get(block.page_type, 50.0)
                            ))
                        elif i < len(lines) - 1 and any(p in line_lower for p in [":", "title"]):
                            if self.name_title_regex.match(lines[i + 1]):
                                candidates.append(DecisionMakerCandidate(
                                    name=lines[i + 1],
                                    title=title_key.title(),
                                    page_url=block.page_url,
                                    page_type=block.page_type,
                                    snippet=f"{line} | {lines[i+1]}",
                                    title_weight=base_weight,
                                    page_weight=PAGE_WEIGHTS.get(block.page_type, 50.0)
                                ))

        return candidates

    def validate_candidates(self, candidates: List[DecisionMakerCandidate]) -> List[DecisionMakerCandidate]:
        """
        Stage 2: Filter out non-leadership candidates, ignored titles, or invalid names.
        Enforces strict person name validation against FORBIDDEN_NAME_PATTERNS.
        """
        valid: List[DecisionMakerCandidate] = []

        for cand in candidates:
            title_clean = cand.title.lower()
            if any(ign in title_clean for ign in IGNORED_TITLES):
                continue

            # Clean trailing title words appended to name
            name_parts = cand.name.split()
            if len(name_parts) > 2 and name_parts[-1].lower() in LEADERSHIP_TITLES:
                cand.name = " ".join(name_parts[:-1])

            tokens = cand.name.lower().split()
            if len(tokens) < 2 or len(tokens) > 4:
                continue
            if not self.name_title_regex.fullmatch(cand.name):
                continue

            # Strict person name validation against forbidden patterns
            if any(w in FORBIDDEN_NAME_PATTERNS for w in tokens):
                continue

            valid.append(cand)

        return valid

    def merge_candidates(
        self, candidates: List[DecisionMakerCandidate]
    ) -> List[Tuple[DecisionMakerCandidate, List[DecisionMakerCandidate]]]:
        """
        Stage 3: Merges candidates discovered across multiple pages into single candidate groups.
        Returns a list of (primary_candidate, all_occurrences).
        """
        grouped: Dict[Tuple[str, str], List[DecisionMakerCandidate]] = {}
        for cand in candidates:
            key = (cand.name.lower(), cand.title.lower())
            grouped.setdefault(key, []).append(cand)

        merged: List[Tuple[DecisionMakerCandidate, List[DecisionMakerCandidate]]] = []
        for key, occurrences in grouped.items():
            primary = occurrences[0]
            merged.append((primary, occurrences))
        return merged

    def score_candidates(
        self,
        merged_candidates: List[Tuple[DecisionMakerCandidate, List[DecisionMakerCandidate]]],
        snapshot: WebsiteSnapshot
    ) -> List[DecisionMakerCandidate]:
        """
        Stage 4: Scores merged candidates with explicit scoring breakdown and evidence deltas.
        """
        if not merged_candidates:
            return []

        scored_list: List[DecisionMakerCandidate] = []

        # Collect all snapshot emails
        all_snapshot_emails: List[str] = []
        email_source_by_address: Dict[str, str] = {}
        for page_url, html in snapshot.pages.items():
            mailto_matches = self.mailto_regex.findall(html)
            raw_matches = self.raw_email_regex.findall(html)
            for email in mailto_matches + raw_matches:
                normalized = normalize_email(email)
                if email_matches_domain(normalized, snapshot.domain):
                    all_snapshot_emails.append(normalized)
                    email_source_by_address.setdefault(normalized, page_url)
        all_snapshot_emails = list(dict.fromkeys(all_snapshot_emails))

        for primary, occurrences in merged_candidates:
            evidence_list: List[DecisionMakerEvidence] = []
            breakdown: Dict[str, float] = {}

            # Base title weight
            title_weight = primary.title_weight
            title_contrib = title_weight * SCORING_WEIGHTS["title_base_multiplier"]
            breakdown["title_weight"] = round(title_contrib, 2)
            evidence_list.append(DecisionMakerEvidence(
                page_url=primary.page_url,
                page_type=primary.page_type,
                title_found=primary.title,
                matched_name=primary.name,
                confidence_delta=title_contrib,
                reason=f"Leadership title base weight for {primary.title}"
            ))

            # Highest page weight
            best_page_weight = max(occ.page_weight for occ in occurrences)
            best_page_occ = max(occurrences, key=lambda x: x.page_weight)
            page_contrib = best_page_weight * SCORING_WEIGHTS["page_base_multiplier"]
            breakdown["page_weight"] = round(page_contrib, 2)
            evidence_list.append(DecisionMakerEvidence(
                page_url=best_page_occ.page_url,
                page_type=best_page_occ.page_type,
                title_found=primary.title,
                matched_name=primary.name,
                confidence_delta=page_contrib,
                reason=f"Highest priority page type match ({best_page_occ.page_type})"
            ))

            total_score = title_contrib + page_contrib

            # Multi-stage email verification with strategy trace
            matched_email = None
            email_strategy = None
            email_weight = 0.0

            for email in all_snapshot_emails:
                if is_generic_email(email):
                    self.stats["generic_emails_rejected"] += 1
                    continue

                matched, strat, weight = match_email_to_name(email, primary.name)
                if matched:
                    matched_email = email
                    email_strategy = strat
                    email_weight = weight
                    break

            if matched_email:
                total_score += email_weight
                breakdown["email_bonus"] = round(email_weight, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=email_source_by_address[matched_email],
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    matched_email=matched_email,
                    confidence_delta=email_weight,
                    reason=f"Verified email via {email_strategy}"
                ))
            else:
                no_email_pen = SCORING_WEIGHTS["no_email_penalty"]
                total_score += no_email_pen
                breakdown["no_email_penalty"] = round(no_email_pen, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=no_email_pen,
                    reason="No verified personal email found on website"
                ))

            # Social profile confirmation
            social_weight = 0.0
            if snapshot.social_profiles:
                social_weight = SCORING_WEIGHTS["social_confirmation"]
                total_score += social_weight
                breakdown["social_bonus"] = round(social_weight, 2)
                self.stats["social_confirmations"] += 1
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=social_weight,
                    reason="Company social profile verification confirmed"
                ))

            # Dual title combo bonus check
            snippet_lower = primary.snippet.lower()
            if any(combo in snippet_lower for combo in [" & ", " and ", " / ", " | "]) and any(kw in snippet_lower for kw in ["founder", "broker", "ceo", "president", "owner"]):
                combo_bonus = SCORING_WEIGHTS.get("dual_title_combo_bonus", 10.0)
                total_score += combo_bonus
                breakdown["dual_title_combo_bonus"] = round(combo_bonus, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=combo_bonus,
                    reason="Dual executive leadership title combination detected"
                ))

            # Repeated appearance check across merged occurrences
            if len(occurrences) > 1:
                repeat_contrib = SCORING_WEIGHTS["repeated_appearance"]
                total_score += repeat_contrib
                breakdown["repeat_bonus"] = round(repeat_contrib, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=repeat_contrib,
                    reason=f"Candidate appeared on {len(occurrences)} distinct pages"
                ))
            elif title_weight < 95.0 or best_page_occ.page_type not in ("about", "team", "leadership", "our-story"):
                single_pen = SCORING_WEIGHTS["single_appearance_penalty"]
                total_score += single_pen
                breakdown["single_appearance_penalty"] = round(single_pen, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type=primary.page_type,
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=single_pen,
                    reason="Candidate appeared on only 1 page"
                ))

            # Footer-only or footer-origin check
            if any(occ.page_type == "footer" for occ in occurrences) and best_page_occ.page_type not in ("about", "team", "leadership", "our-story"):
                footer_pen = SCORING_WEIGHTS["footer_only_penalty"]
                total_score += footer_pen
                breakdown["footer_penalty"] = round(footer_pen, 2)
                evidence_list.append(DecisionMakerEvidence(
                    page_url=primary.page_url,
                    page_type="footer",
                    title_found=primary.title,
                    matched_name=primary.name,
                    confidence_delta=footer_pen,
                    reason="Candidate found in footer element without team/about listing"
                ))

            breakdown["final_score"] = round(max(0.0, min(100.0, total_score)), 2)

            final_cand = DecisionMakerCandidate(
                name=primary.name,
                title=primary.title,
                page_url=primary.page_url,
                page_type=primary.page_type,
                snippet=primary.snippet,
                matched_email=matched_email,
                email_matching_strategy=email_strategy,
                title_weight=title_weight,
                page_weight=best_page_weight,
                email_weight=email_weight,
                social_weight=social_weight,
                score=max(0.0, min(100.0, total_score)),
                evidence=evidence_list,
                scoring_breakdown=breakdown
            )
            scored_list.append(final_cand)

        scored_list.sort(key=lambda c: c.score, reverse=True)
        return scored_list

    def detect_conflicts(self, candidates: List[DecisionMakerCandidate]) -> List[Dict[str, Any]]:
        """
        Stage 5: Detects competing high-confidence leadership candidates.
        """
        conflicts = []
        if len(candidates) > 1:
            top_score = candidates[0].score
            for cand in candidates[1:]:
                if cand.score >= top_score * 0.8 and cand.name != candidates[0].name:
                    conflicts.append({
                        "candidate_name": cand.name,
                        "title": cand.title,
                        "score": round(cand.score, 2),
                        "reason": f"Competing decision maker candidate with high score ({cand.score:.1f} vs top {top_score:.1f})"
                    })
        return conflicts

    def select_winner(
        self,
        candidates: List[DecisionMakerCandidate],
        conflicts: List[Dict[str, Any]],
        snapshot: WebsiteSnapshot
    ) -> DecisionMaker:
        """
        Stage 6: Selects primary decision maker, enforces MIN_CONFIDENCE_THRESHOLD,
        and constructs final DecisionMaker model output with INTEGER confidence score.
        """
        if not candidates:
            self.stats["no_decision_maker"] += 1
            return DecisionMaker(
                decision_maker_name=None,
                decision_maker_title=None,
                decision_maker_source=None,
                confidence_score=0,
                verified_email=None,
                email_source=None,
                email_verified=False,
                status="NO_DECISION_MAKER",
                evidence=[],
                conflicts=[],
                decision_makers=[]
            )

        winner = candidates[0]
        final_int_confidence = int(round(max(0.0, min(100.0, winner.score))))

        # Enforce Minimum Confidence Threshold
        if final_int_confidence < MIN_CONFIDENCE_THRESHOLD:
            self.stats["no_decision_maker"] += 1
            return DecisionMaker(
                decision_maker_name=None,
                decision_maker_title=None,
                decision_maker_source=winner.page_url,
                confidence_score=final_int_confidence,
                verified_email=None,
                email_source=None,
                email_verified=False,
                status="NO_DECISION_MAKER",
                evidence=[asdict(e) for e in winner.evidence],
                conflicts=conflicts,
                decision_makers=[asdict(c) for c in candidates]
            )

        winner.is_primary = True
        status = "FOUND" if winner.matched_email else "NO_EMAIL_FOUND"
        email_source = None
        if winner.matched_email:
            self.stats["verified_emails"] += 1
            email_source = next(
                (
                    evidence.page_url
                    for evidence in winner.evidence
                    if evidence.matched_email == winner.matched_email
                ),
                None
            )

        return DecisionMaker(
            decision_maker_name=winner.name,
            decision_maker_title=winner.title,
            decision_maker_source=winner.page_url,
            confidence_score=final_int_confidence,
            verified_email=winner.matched_email,
            email_source=email_source,
            email_verified=winner.matched_email is not None,
            status=status,
            evidence=[asdict(e) for e in winner.evidence],
            conflicts=conflicts,
            decision_makers=[asdict(c) for c in candidates]
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Exposes diagnostic metrics for reporting and debugging.
        """
        total_p = self.stats["companies_processed"]
        avg_conf = (self.stats["total_confidence"] / total_p) if total_p > 0 else 0.0
        avg_time = (self.stats["total_processing_time_ms"] / total_p) if total_p > 0 else 0.0

        res = dict(self.stats)
        res["average_confidence"] = int(round(avg_conf))
        res["avg_processing_time_ms"] = round(avg_time, 2)
        res["fastest_time_ms"] = round(self.stats["fastest_time_ms"], 2) if total_p > 0 else 0.0
        res["slowest_time_ms"] = round(self.stats["slowest_time_ms"], 2)
        return res

    def _compute_content_hash(self, snapshot: WebsiteSnapshot) -> str:
        """
        Computes SHA-256 hash derived from pages, URLs, social profiles, and CONFIG_VERSION.
        """
        raw_str = f"{CONFIG_VERSION}:{snapshot.domain}:{sorted(snapshot.pages.items())}:{sorted(snapshot.social_profiles.items())}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def _read_hashed_cache(self, domain: str, content_hash: str) -> Optional[DecisionMaker]:
        if not domain or domain == "unknown":
            return None
        file_path = self.cache_dir / f"{domain}_{content_hash[:16]}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return DecisionMaker(**data)
            except Exception as e:
                logger.warning(f"Failed to read cache file {file_path}: {e}")
                self.stats["cache_invalidations"] += 1
        return None

    def _write_hashed_cache(self, domain: str, content_hash: str, dm: DecisionMaker) -> None:
        if not domain or domain == "unknown":
            return
        file_path = self.cache_dir / f"{domain}_{content_hash[:16]}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(dm), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write cache file {file_path}: {e}")

    def _update_timing_stats(self, duration_ms: float) -> None:
        self.stats["total_processing_time_ms"] += duration_ms
        if duration_ms < self.stats["fastest_time_ms"]:
            self.stats["fastest_time_ms"] = duration_ms
        if duration_ms > self.stats["slowest_time_ms"]:
            self.stats["slowest_time_ms"] = duration_ms

    def _build_website_snapshot(self, lead: Lead, domain_cache: Dict[str, Any]) -> WebsiteSnapshot:
        domain = ""
        if lead.website:
            parsed = urlparse(lead.website)
            domain = (parsed.netloc or parsed.path).lower().strip()

        pages: Dict[str, str] = {}
        extraction_res = domain_cache.get(domain) if domain else None
        if extraction_res:
            html_list = getattr(extraction_res, "html_pages", []) or []
            page_urls = getattr(extraction_res, "html_page_urls", []) or []
            for idx, html_text in enumerate(html_list):
                url = page_urls[idx] if idx < len(page_urls) else ""
                if not url:
                    url = f"{lead.website}/page_{idx}" if lead.website else f"http://{domain}/page_{idx}"
                pages[url] = html_text

        socials = lead.social_profiles or {}
        return WebsiteSnapshot(
            domain=domain,
            pages=pages,
            social_profiles=socials
        )

    def _update_lead_with_decision_maker(self, lead: Lead, dm: DecisionMaker) -> Lead:
        from dataclasses import replace
        return replace(
            lead,
            owner_name=dm.decision_maker_name,
            owner_title=dm.decision_maker_title,
            owner_email=dm.verified_email,
            decision_maker=dm
        )
