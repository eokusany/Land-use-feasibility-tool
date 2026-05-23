"""Tests for the Calgary zoning provider and its integration with PolicyRetrieval.

Mocked fixtures are captured from the real Socrata schema verified on
2026-05-23 (https://data.calgary.ca/resource/qe6k-p9nh.json).

Run all (mocked, fast):
    python -m unittest test_calgary_provider.py -v

Include live integration test against the real API:
    RUN_LIVE_TESTS=1 python -m unittest test_calgary_provider.py -v
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from policy_retrieval import PolicyRetrieval
from zoning_providers import get_provider
from zoning_providers.base import ProviderError, ZoningResult
from zoning_providers.calgary import CalgaryZoningProvider


# ---------------------------------------------------------------------------
# Helpers — fake HTTP responses
# ---------------------------------------------------------------------------


def _mock_response(json_data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    return m


# Schema captured from the live API on 2026-05-23.
ZONE_HIT = [{
    "lu_bylaw": "1",
    "lu_code": "C-C1",
    "label": "C-C1",
    "description": "Commercial - Community 1",
    "major": "Commercial",
    "generalize": "Community Commercial",
}]

# Direct Control (site-specific) zone
DC_HIT = [{
    "lu_bylaw": "1",
    "lu_code": "DC",
    "label": "DC",
    "description": "Direct Control District",
    "major": "Direct Control",
    "generalize": "Direct Control",
}]

# Residential zone — verifies handling of dashed codes (R-G, R-CG, etc.)
RG_HIT = [{
    "lu_bylaw": "1",
    "lu_code": "R-G",
    "label": "R-G",
    "description": "Residential - Grade-Oriented Infill",
    "major": "Residential",
    "generalize": "Residential",
}]


# ---------------------------------------------------------------------------
# Provider unit tests (mocked)
# ---------------------------------------------------------------------------


class CalgaryProviderUnitTests(unittest.TestCase):

    def setUp(self):
        self.provider = CalgaryZoningProvider()

    def test_successful_lookup_returns_zone(self):
        # Downtown Calgary, near city hall
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ZONE_HIT)
            result = self.provider.lookup(51.0447, -114.0631)

        self.assertIsInstance(result, ZoningResult)
        self.assertEqual(result.zone_code, "C-C1")
        self.assertEqual(result.zone_name, "Commercial - Community 1")
        self.assertIn("Calgary", result.source)
        self.assertIn("calgary.ca", result.source_url)
        self.assertTrue(result.bylaw_section_url)
        self.assertTrue(result.retrieved_at)
        self.assertEqual(result.overlays, [])  # Calgary doesn't expose overlays
        self.assertEqual(result.provider_notes, [])  # not a DC zone

    def test_no_polygon_hit_returns_none(self):
        """Coordinates outside Calgary — Socrata returns []."""
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            result = self.provider.lookup(43.6532, -79.3832)  # Toronto
        self.assertIsNone(result)

    def test_dc_zone_attaches_provider_note(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(DC_HIT)
            result = self.provider.lookup(51.05, -114.07)

        self.assertEqual(result.zone_code, "DC")
        self.assertTrue(result.provider_notes, "DC zone should attach a site-specific note")
        self.assertIn("site-specific", result.provider_notes[0].lower())

    def test_dashed_zone_family_is_resolved_correctly(self):
        """R-G belongs to the R family, NOT 'R-G' literally."""
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(RG_HIT)
            result = self.provider.lookup(51.05, -114.07)

        self.assertEqual(result.zone_code, "R-G")
        # R-G is not site-specific — no provider note
        self.assertEqual(result.provider_notes, [])

    def test_network_error_raises_provider_error(self):
        import requests as _r
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = _r.ConnectionError("offline")
            with self.assertRaises(ProviderError) as ctx:
                self.provider.lookup(51.0447, -114.0631)
            self.assertIn("Calgary", str(ctx.exception))

    def test_http_500_raises_provider_error(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([], status=500)
            with self.assertRaises(ProviderError):
                self.provider.lookup(51.0447, -114.0631)

    def test_socrata_error_object_raises_provider_error(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(
                {"error": True, "message": "Invalid SoQL query"}
            )
            with self.assertRaises(ProviderError):
                self.provider.lookup(51.0447, -114.0631)

    def test_polygon_hit_with_empty_zone_code_raises(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(
                [{"lu_code": "", "description": "?"}]
            )
            with self.assertRaises(ProviderError):
                self.provider.lookup(51.0447, -114.0631)

    def test_missing_coordinates_returns_none(self):
        self.assertIsNone(self.provider.lookup(None, -114.0631))
        self.assertIsNone(self.provider.lookup(51.0447, None))

    def test_fallback_to_generalize_when_description_missing(self):
        """If description is empty, zone_name should fall back."""
        hit = [{
            "lu_code": "M-CG",
            "description": "",
            "major": "Multi-Residential",
            "generalize": "Multi-Residential Grade",
        }]
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(hit)
            result = self.provider.lookup(51.05, -114.07)

        self.assertEqual(result.zone_code, "M-CG")
        self.assertEqual(result.zone_name, "Multi-Residential Grade")


# ---------------------------------------------------------------------------
# Registry integration
# ---------------------------------------------------------------------------


class CalgaryRegistryTests(unittest.TestCase):

    def test_get_provider_calgary_case_insensitive(self):
        for name in ("Calgary", "calgary", "  CALGARY  "):
            self.assertIsInstance(get_provider(name), CalgaryZoningProvider)


class PolicyRetrievalCalgaryIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.pr = PolicyRetrieval()
        self.muni = {
            "name": "Calgary",
            "province": "AB",
            "land_use_bylaw": "https://www.calgary.ca/planning/land-use/bylaw-1p2007.html",
        }
        self.prop_with_coords = {
            "raw_input": {"address": "800 Macleod Trail SE"},
            "coordinates": {"latitude": 51.0447, "longitude": -114.0631},
        }

    def test_verified_path_populates_zone_fields(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(ZONE_HIT)
            policy = self.pr.get_land_use_policies(self.muni, self.prop_with_coords)

        self.assertEqual(policy["verification_status"], "verified")
        self.assertFalse(policy["verification_required"])
        self.assertEqual(policy["zoning_code"], "C-C1")
        self.assertIn("Commercial", policy["zoning"])
        self.assertIn("Calgary", policy["zone_source"])
        # Still no fabricated setbacks/uses
        self.assertEqual(policy["setbacks"], {})
        self.assertEqual(policy["permitted_uses"], [])


# ---------------------------------------------------------------------------
# Live integration test — gated by env var
# ---------------------------------------------------------------------------


@unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS"), "Set RUN_LIVE_TESTS=1 to hit the real API")
class LiveCalgaryAPITests(unittest.TestCase):

    def test_live_downtown_lookup(self):
        provider = CalgaryZoningProvider()
        # Calgary City Hall area
        result = provider.lookup(51.0453, -114.0581)
        self.assertIsNotNone(result, "downtown Calgary should hit a polygon")
        self.assertTrue(result.zone_code)
        print(f"\n  Calgary downtown live result: {result.zone_code} — {result.zone_name}")

    def test_live_outside_calgary_returns_none(self):
        provider = CalgaryZoningProvider()
        # Edmonton coordinates
        result = provider.lookup(53.5444, -113.4909)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
