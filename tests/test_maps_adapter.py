"""Offline adapter tests for the Google Maps Apify payload mapping."""

from __future__ import annotations

import unittest

from src.mappers import build_maps_actor_input, dict_to_raw_lead, raw_lead_to_lead


class BuildMapsActorInputTests(unittest.TestCase):
    """Cover johnvc input vs the legacy compass-style payload."""

    def test_live_actor_uses_search_terms(self) -> None:
        """johnvc/google-maps-places-api takes searchTerms and a 20-place floor."""
        payload = build_maps_actor_input(
            "johnvc/google-maps-places-api",
            ["coffee in Austin TX"],
            5,
        )
        self.assertEqual(payload["searchTerms"], ["coffee in Austin TX"])
        self.assertEqual(payload["maxResultsPerSearch"], 20)
        self.assertNotIn("searchStringsArray", payload)

    def test_legacy_actor_keeps_compass_fields(self) -> None:
        """An env override to a compass-style Actor keeps the old input shape."""
        payload = build_maps_actor_input(
            "compass/google-maps-scraper",
            ["coffee in Austin TX"],
            50,
        )
        self.assertEqual(payload["searchStringsArray"], ["coffee in Austin TX"])
        self.assertEqual(payload["maxCrawledPlacesPerSearch"], 50)


class DictToRawLeadTests(unittest.TestCase):
    """Cover johnvc output fields mapped onto RawLead names."""

    def test_phone_rating_and_coordinates(self) -> None:
        """phoneNumber/rating/ratingCount/lat/lng become the repo's field names."""
        raw = dict_to_raw_lead(
            {
                "title": "Cafe",
                "address": "1 Main St",
                "website": "https://example.com",
                "phoneNumber": "512-555-0100",
                "rating": 4.6,
                "ratingCount": 120,
                "latitude": 30.27,
                "longitude": -97.74,
                "placeId": "abc",
                "searchTerm": "coffee in Austin TX",
                "type": "Cafe",
                "types": ["cafe", "restaurant"],
            }
        )
        self.assertEqual(raw.phone, "512-555-0100")
        self.assertEqual(raw.totalScore, 4.6)
        self.assertEqual(raw.reviewsCount, 120)
        self.assertEqual(raw.location, {"lat": 30.27, "lng": -97.74})
        self.assertEqual(raw.searchString, "coffee in Austin TX")
        self.assertEqual(raw.categoryName, "Cafe")
        lead = raw_lead_to_lead(raw)
        self.assertEqual(lead.phone, "512-555-0100")
        self.assertEqual(lead.rating, 4.6)
        self.assertEqual(lead.review_count, 120)
        self.assertEqual(lead.latitude, 30.27)
        self.assertEqual(lead.longitude, -97.74)


if __name__ == "__main__":
    unittest.main()
