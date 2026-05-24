"""
Tests for the Edmonton zoning provider and its integration with PolicyRetrieval.

Run all (mocked, fast):
    python -m unittest test_edmonton_provider.py -v

Include live integration tests against the real Edmonton open-data API:
    RUN_LIVE_TESTS=1 python -m unittest test_edmonton_provider.py -v
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from policy_retrieval import PolicyRetrieval
from zoning_providers import get_provider
from zoning_providers.base import ProviderError, ZoningResult
from zoning_providers.edmonton import EdmontonZoningProvider


# ---------------------------------------------------------------------------
# Helpers — fake HTTP responses
# ---------------------------------------------------------------------------

def _mock_response(json_data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    return m


# Captured from a real query at downtown Edmonton (Churchill Square area).
ZONE_HIT = [{
    "id": "12345",
    "zoning": "CCA",
    "description": "Core Commercial Arts Zone",
    "url": "https://zoningbylaw.edmonton.ca/part-3-special-area-zones/downtown-special-area/327-cca-core-commercial-arts-zone",
}]

OVERLAYS_HIT = [
    {"overlay_code": "DN", "overlay_descr": "Downtown Special Area", "bylaw_no": "12800"},
    {"overlay_code": "EDC", "overlay_descr": "Edmonton Design Committee", "bylaw_no": "12190"},
]

DC2_HIT = [{
    "id": "171557",
    "zoning": "DC2",
    "description": "Site Specific Development Control Provision",
    "url": "https://zoningbylaw.edmonton.ca/dc2-820",
}]


# ---------------------------------------------------------------------------
# Provider unit tests (mocked)
# ---------------------------------------------------------------------------

class EdmontonProviderUnitTests(unittest.TestCase):

    def setUp(self):
        self.provider = EdmontonZoningProvider()

    def test_successful_lookup_returns_zone_and_overlays(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(ZONE_HIT),
                _mock_response(OVERLAYS_HIT),
            ]
            result = self.provider.lookup(53.5444, -113.4909)

        self.assertIsInstance(result, ZoningResult)
        self.assertEqual(result.zone_code, "CCA")
        self.assertEqual(result.zone_name, "Core Commercial Arts Zone")
        self.assertIn("zoningbylaw.edmonton.ca", result.bylaw_section_url)
        self.assertEqual(len(result.overlays), 2)
        self.assertEqual(result.overlays[0].code, "DN")
        self.assertTrue(result.retrieved_at)  # ISO timestamp present
        self.assertIn("Edmonton", result.source)

    def test_no_polygon_hit_returns_none(self):
        """Query outside Edmonton — Socrata returns []."""
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            result = self.provider.lookup(43.6532, -79.3832)  # Toronto
        self.assertIsNone(result)

    def test_dc2_zone_attaches_provider_note(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(DC2_HIT),
                _mock_response([]),
            ]
            result = self.provider.lookup(53.5556, -113.4715)

        self.assertEqual(result.zone_code, "DC2")
        self.assertTrue(result.provider_notes, "DC2 should attach a site-specific note")
        self.assertIn("site", result.provider_notes[0].lower())

    def test_overlay_failure_does_not_break_zone_lookup(self):
        """If overlays endpoint errors, we still return the base zone."""
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(ZONE_HIT),
                _mock_response({"error": True, "message": "boom"}),  # overlays fail
            ]
            result = self.provider.lookup(53.5444, -113.4909)

        self.assertIsNotNone(result)
        self.assertEqual(result.zone_code, "CCA")
        self.assertEqual(result.overlays, [])

    def test_network_error_raises_provider_error(self):
        import requests as _r
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = _r.ConnectionError("nope")
            with self.assertRaises(ProviderError):
                self.provider.lookup(53.5444, -113.4909)

    def test_http_500_raises_provider_error(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([], status=500)
            with self.assertRaises(ProviderError):
                self.provider.lookup(53.5444, -113.4909)

    def test_socrata_error_object_raises_provider_error(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response({"error": True, "message": "bad query"})
            with self.assertRaises(ProviderError):
                self.provider.lookup(53.5444, -113.4909)

    def test_polygon_hit_with_empty_zone_code_raises(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([{"zoning": "", "description": "?", "url": ""}])
            with self.assertRaises(ProviderError):
                self.provider.lookup(53.5444, -113.4909)

    def test_missing_coordinates_returns_none(self):
        self.assertIsNone(self.provider.lookup(None, -113.4909))
        self.assertIsNone(self.provider.lookup(53.5444, None))


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class RegistryTests(unittest.TestCase):

    def test_get_provider_edmonton_case_insensitive(self):
        for name in ("Edmonton", "edmonton", "  EDMONTON  "):
            self.assertIsInstance(get_provider(name), EdmontonZoningProvider)

    def test_get_provider_unknown_returns_none(self):
        self.assertIsNone(get_provider("Atlantis"))
        self.assertIsNone(get_provider(""))
        self.assertIsNone(get_provider(None))


# ---------------------------------------------------------------------------
# PolicyRetrieval integration tests (mocked provider)
# ---------------------------------------------------------------------------

class PolicyRetrievalIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.pr = PolicyRetrieval()
        self.muni = {
            "name": "Edmonton",
            "province": "AB",
            "land_use_bylaw": "https://www.edmonton.ca/city_government/bylaws/zoning-bylaw",
        }
        self.prop_with_coords = {
            "raw_input": {"address": "1 Sir Winston Churchill Sq"},
            "coordinates": {"latitude": 53.5444, "longitude": -113.4909},
        }
        self.prop_no_coords = {
            "raw_input": {"address": "address that fails geocoding"},
        }

    def test_verified_path_populates_zone_fields(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(ZONE_HIT),
                _mock_response(OVERLAYS_HIT),
            ]
            policy = self.pr.get_land_use_policies(self.muni, self.prop_with_coords)

        self.assertEqual(policy["verification_status"], "verified")
        self.assertFalse(policy["verification_required"])
        self.assertEqual(policy["zoning_code"], "CCA")
        self.assertIn("Core Commercial Arts", policy["zoning"])
        self.assertEqual(len(policy["zone_overlays"]), 2)
        self.assertIn("Edmonton", policy["zone_source"])
        self.assertTrue(policy["zone_retrieved_at"])
        # Critically: we still don't fabricate setbacks/uses
        self.assertEqual(policy["setbacks"], {})
        self.assertEqual(policy["permitted_uses"], [])

    def test_no_coordinates_marks_provider_failed(self):
        policy = self.pr.get_land_use_policies(self.muni, self.prop_no_coords)
        self.assertEqual(policy["verification_status"], "provider_failed")
        self.assertTrue(policy["verification_required"])
        self.assertIsNone(policy["zoning"])
        self.assertIn("coordinates", policy["verification_message"].lower())

    def test_provider_network_failure_falls_back_gracefully(self):
        import requests as _r
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = _r.ConnectionError("offline")
            policy = self.pr.get_land_use_policies(self.muni, self.prop_with_coords)

        self.assertEqual(policy["verification_status"], "provider_failed")
        self.assertTrue(policy["verification_required"])
        self.assertIsNone(policy["zoning"])
        self.assertIn("unavailable", policy["verification_message"])

    def test_outside_coverage_marks_outside_coverage(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])  # no polygon hit
            policy = self.pr.get_land_use_policies(
                self.muni,
                {"raw_input": {"address": "x"}, "coordinates": {"latitude": 43.65, "longitude": -79.38}},
            )

        self.assertEqual(policy["verification_status"], "outside_coverage")
        self.assertTrue(policy["verification_required"])
        self.assertIn("not fall inside", policy["verification_message"])

    def test_unknown_municipality_stays_in_option_a_mode(self):
        muni = {"name": "Smalltown", "province": "AB"}
        prop = {"raw_input": {"address": "1 Main"}, "coordinates": {"latitude": 50, "longitude": -113}}
        policy = self.pr.get_land_use_policies(muni, prop)

        self.assertEqual(policy["verification_status"], "unverified")
        self.assertTrue(policy["verification_required"])
        self.assertIsNone(policy["zoning"])

    def test_verified_path_includes_parcel_context(self):
        """When a parcel context is available, policy_info gains a `parcel_context` key."""
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(ZONE_HIT),       # zone lookup
                _mock_response(OVERLAYS_HIT),   # overlays
                _mock_response([]),             # parcel
                _mock_response([]),             # permits
                _mock_response([]),             # heritage
                _mock_response([]),             # flood
                _mock_response([]),             # neighbour zones
            ]
            policy = self.pr.get_land_use_policies(self.muni, self.prop_with_coords)
        self.assertIn("parcel_context", policy)
        pc = policy["parcel_context"]
        self.assertIsInstance(pc, dict)
        self.assertIn("lot", pc)
        self.assertIn("permits", pc)
        self.assertIn("adjacent_zones", pc)
        self.assertIn("overlay_flags", pc)
        self.assertIn("aerial_image", pc)
        self.assertIn("warnings", pc)

    def test_context_failure_does_not_downgrade_verification(self):
        """A blown-up context() must NOT change verification_status."""
        class _Boom(Exception):
            pass

        with patch("zoning_providers.base.requests.get") as mock_get, \
             patch(
                 "zoning_providers.edmonton.EdmontonZoningProvider.context",
                 side_effect=_Boom("explode"),
             ):
            mock_get.side_effect = [
                _mock_response(ZONE_HIT),
                _mock_response(OVERLAYS_HIT),
            ]
            policy = self.pr.get_land_use_policies(self.muni, self.prop_with_coords)
        self.assertEqual(policy["verification_status"], "verified")
        self.assertIn("parcel_context", policy)
        self.assertTrue(any("context" in w.lower() for w in policy["parcel_context"]["warnings"]))


# ---------------------------------------------------------------------------
# Live integration test — gated by env var so CI doesn't hammer the city
# ---------------------------------------------------------------------------

@unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS"), "Set RUN_LIVE_TESTS=1 to hit the real API")
class LiveEdmontonAPITests(unittest.TestCase):

    def test_live_downtown_lookup(self):
        provider = EdmontonZoningProvider()
        result = provider.lookup(53.5444, -113.4909)  # Churchill Square
        self.assertIsNotNone(result, "downtown should hit a polygon")
        self.assertTrue(result.zone_code)
        self.assertTrue(result.zone_name)
        self.assertTrue(result.bylaw_section_url and "edmonton" in result.bylaw_section_url)
        print(f"\n  Downtown live result: {result.zone_code} — {result.zone_name}")

    def test_live_outside_edmonton_returns_none(self):
        provider = EdmontonZoningProvider()
        result = provider.lookup(43.6532, -79.3832)  # Toronto
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
