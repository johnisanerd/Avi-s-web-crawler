"""Regression coverage for contact and owner extraction production paths."""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.decision_maker_intelligence import DecisionMakerIntelligence
from src.email_extractor import EmailExtractor, ExtractionResult
from src.html_parser import parse_html_to_blocks
from src.models import Lead


class TestEmailExtractionRegressions(unittest.TestCase):
    @patch("requests.Session.get")
    def test_homepage_vendor_email_does_not_stop_subpage_discovery(self, mock_get):
        mock_home = MagicMock()
        mock_home.status_code = 200
        mock_home.text = "<footer>support@vendor.com</footer>"
        mock_contact = MagicMock()
        mock_contact.status_code = 200
        mock_contact.text = "<p>john@testsite.com</p>"
        mock_get.side_effect = [mock_home, mock_contact]

        result = EmailExtractor(max_pages=2).extract_from_website("http://testsite.com")

        self.assertEqual(result.best_email, "john@testsite.com")
        self.assertNotIn("support@vendor.com", result.emails)
        self.assertEqual(result.html_page_urls, [
            "http://testsite.com/",
            "http://testsite.com/contact",
        ])
        self.assertEqual(
            result.email_sources["john@testsite.com"],
            "http://testsite.com/contact",
        )
        self.assertEqual(mock_get.call_count, 2)

    def test_owner_detection_rejects_lowercase_sentence_fragments(self):
        extractor = EmailExtractor()

        self.assertEqual(
            extractor._detect_owner("<p>Owner may finance with approved lender</p>", []),
            (None, None, None),
        )
        self.assertEqual(
            extractor._detect_owner("<p>Owner on day of closing</p>", []),
            (None, None, None),
        )


    def test_parser_rejects_or_recovers_concatenated_email_noise(self):
        extractor = EmailExtractor()
        html = """
        <a href="tel:+4994185080172oderinfo@realtysite.com">
            +49 941 850 801 72 oder info@realtysite.com
        </a>
        <script>
            {"description": "Phone913.393.9469EmailDavid@RealtySite.com"}
        </script>
        <img src="flags@2x.png">
        <p>you@gmail.com</p>
        """

        self.assertEqual(
            extractor._parse_emails(html),
            ["info@realtysite.com", "David@RealtySite.com"],
        )

    def test_ranking_keeps_alternate_contacts_but_rejects_platform_noise(self):
        extractor = EmailExtractor()

        ranked = extractor._rank_emails(
            [
                "support@agentfire.com",
                "bouncedemail@boomtownroi.com",
                "campaigns@info.properties",
                "owner@gmail.com",
                "info@realtysite.com",
                "jane@realtysite.com",
            ],
            "realtysite.com",
        )

        self.assertEqual(
            ranked,
            ["jane@realtysite.com", "owner@gmail.com", "info@realtysite.com"],
        )


class TestDecisionMakerProductionRegressions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = DecisionMakerIntelligence(
            cache_dir=Path(self.temp_dir) / "decision-maker-cache"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @staticmethod
    def _lead(**overrides):
        values = {
            "business_name": "Example Realty",
            "category": "Broker",
            "website": "http://example.com",
            "phone": "",
            "street": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "country": "",
            "rating": 0.0,
            "review_count": 0,
            "latitude": None,
            "longitude": None,
            "google_maps_url": "",
            "google_place_id": None,
            "source_queries": set(),
        }
        values.update(overrides)
        return Lead(**values)

    def test_sentence_fragment_is_not_accepted_as_owner_name(self):
        blocks = parse_html_to_blocks(
            "http://example.com/about",
            "<p>Owner may finance with approved lender</p>",
        )

        candidates = self.engine.extract_candidates(blocks)
        validated = self.engine.validate_candidates(candidates)

        self.assertEqual(validated, [])

    def test_real_page_and_email_sources_are_preserved(self):
        html = """
        <div class="team-member">
            <h2>Jane Doe</h2>
            <p>Owner</p>
            <a href="mailto:jane@vendor.com">Vendor</a>
            <a href="mailto:jane@example.com">Email Jane</a>
        </div>
        """
        extraction = ExtractionResult(
            emails=["jane@example.com"],
            best_email="jane@example.com",
            owner_name=None,
            owner_title=None,
            owner_email=None,
            html_pages=[html],
            html_page_urls=["http://example.com/team"],
        )

        updated = self.engine.analyze_leads(
            [self._lead()], {"example.com": extraction}
        )[0]

        self.assertEqual(updated.owner_name, "Jane Doe")
        self.assertEqual(updated.owner_email, "jane@example.com")
        self.assertEqual(
            updated.decision_maker.decision_maker_source,
            "http://example.com/team",
        )
        self.assertEqual(
            updated.decision_maker.email_source,
            "http://example.com/team",
        )

    def test_valid_owner_without_email_has_no_email_source(self):
        extraction = ExtractionResult(
            emails=[],
            best_email=None,
            owner_name=None,
            owner_title=None,
            owner_email=None,
            html_pages=["<p>Jane Doe - Owner</p>"],
            html_page_urls=["http://example.com/about"],
        )

        updated = self.engine.analyze_leads(
            [self._lead()], {"example.com": extraction}
        )[0]

        self.assertEqual(updated.owner_name, "Jane Doe")
        self.assertIsNone(updated.owner_email)
        self.assertIsNone(updated.decision_maker.email_source)
        self.assertEqual(updated.decision_maker.status, "NO_EMAIL_FOUND")

    def test_rejected_decision_maker_clears_legacy_owner_guess(self):
        extraction = ExtractionResult(
            emails=[],
            best_email=None,
            owner_name=None,
            owner_title=None,
            owner_email=None,
            html_pages=["<p>Owner may finance with approved lender</p>"],
            html_page_urls=["http://example.com/about"],
        )
        lead = self._lead(
            owner_name="may finance with",
            owner_title="Owner",
            owner_email="support@vendor.com",
        )

        updated = self.engine.analyze_leads(
            [lead], {"example.com": extraction}
        )[0]

        self.assertIsNone(updated.owner_name)
        self.assertIsNone(updated.owner_title)
        self.assertIsNone(updated.owner_email)
        self.assertEqual(updated.decision_maker.status, "NO_DECISION_MAKER")


if __name__ == "__main__":
    unittest.main()
