"""Regression tests for the parser/lookup cleanup pass.

Covers the bugs documented in OPTION_B_TODO.md "Related cleanup":
- _parse_address now extracts unit numbers
- _extract_property_details uses word boundaries
- _extract_municipality_hints uses word boundaries
- _extract_names filters against a stoplist
"""

import unittest
from unittest.mock import patch

from municipality_lookup import MunicipalityLookup
from policy_retrieval import CACHE_TTL_SECONDS, PolicyRetrieval
from property_parser import PropertyParser


class UnitNumberExtractionTests(unittest.TestCase):
    def setUp(self):
        self.parser = PropertyParser()

    def test_trailing_unit_after_comma(self):
        parsed = self.parser._parse_address("8520 Jasper Ave, 1403")
        self.assertEqual(parsed["components"].get("unit"), "1403")

    def test_apt_prefix(self):
        parsed = self.parser._parse_address("Apt 502, 100 Main St")
        self.assertEqual(parsed["components"].get("unit"), "502")

    def test_suite_prefix(self):
        parsed = self.parser._parse_address("Suite 200 - 250 Bay Street")
        self.assertEqual(parsed["components"].get("unit"), "200")

    def test_hash_prefix(self):
        parsed = self.parser._parse_address("#7B, 555 Robson Street")
        self.assertEqual(parsed["components"].get("unit"), "7B")

    def test_postal_code_is_not_a_unit(self):
        parsed = self.parser._parse_address("123 Main St, T5J 0R8")
        # postal_code should be captured separately, NOT as a unit
        self.assertEqual(parsed["components"].get("postal_code"), "T5J0R8")
        self.assertIsNone(parsed["components"].get("unit"))

    def test_no_unit_for_plain_address(self):
        parsed = self.parser._parse_address("100 Main Street")
        self.assertIsNone(parsed["components"].get("unit"))


class PropertyDetailWordBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.parser = PropertyParser()

    def test_non_residential_does_not_match_residential(self):
        details = self.parser._extract_property_details(
            "This is a non-residential industrial lot"
        )
        self.assertNotIn("residential", details.get("zoning_hints", []))
        self.assertIn("industrial", details.get("zoning_hints", []))

    def test_presidential_does_not_match_residential(self):
        details = self.parser._extract_property_details("Near the presidential library")
        self.assertNotIn("residential", details.get("zoning_hints", []))

    def test_residential_matches_standalone_word(self):
        details = self.parser._extract_property_details("Residential property")
        self.assertIn("residential", details.get("zoning_hints", []))

    def test_cottage_singular_now_matches(self):
        details = self.parser._extract_property_details("Plan to build one cottage")
        self.assertIn("cottage", details.get("development_intentions", []))


class MunicipalityHintWordBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.parser = PropertyParser()

    def test_lac_does_not_match_inside_place(self):
        # "Place" must not pull in "Lac la Biche" or similar `Lac` cities
        hints = self.parser._extract_municipality_hints(
            "100 Place du Marché, Montreal"
        )
        self.assertNotIn("Lac la Biche", hints)
        self.assertIn("Montreal", hints)

    def test_mount_does_not_match_inside_paramount(self):
        hints = self.parser._extract_municipality_hints(
            "1 Paramount Way, Calgary"
        )
        # Should NOT contain any "Mount Royal" / "Mount Pearl" hits
        self.assertNotIn("Mount Royal", hints)
        self.assertNotIn("Mount Pearl", hints)
        self.assertIn("Calgary", hints)

    def test_known_city_matches(self):
        hints = self.parser._extract_municipality_hints(
            "Some property in Edmonton, Alberta"
        )
        self.assertIn("Edmonton", hints)


class MunicipalityLookupNameExtractionTests(unittest.TestCase):
    def setUp(self):
        self.lookup = MunicipalityLookup()

    def test_extract_names_filters_stoplist(self):
        names = self.lookup._extract_names(
            "8520 Jasper Avenue North, Edmonton, Alberta"
        )
        # Stoplisted: Avenue, North, Alberta
        self.assertNotIn("Avenue", names)
        self.assertNotIn("North", names)
        self.assertNotIn("Alberta", names)
        # Real candidate retained
        self.assertIn("Edmonton", names)

    def test_extract_names_handles_empty(self):
        self.assertEqual(self.lookup._extract_names(""), [])


class PolicyCacheTests(unittest.TestCase):
    def setUp(self):
        self.pr = PolicyRetrieval()
        self.muni = {"name": "Smalltown", "province": "AB"}
        self.prop = {
            "raw_input": {"address": "1 Main St", "legal_description": "", "additional_info": ""}
        }

    def test_cache_hit_returns_same_instance(self):
        first = self.pr.get_land_use_policies(self.muni, self.prop)
        second = self.pr.get_land_use_policies(self.muni, self.prop)
        self.assertIs(first, second)

    def test_cache_expires_after_ttl(self):
        first = self.pr.get_land_use_policies(self.muni, self.prop)
        # Manually expire the entry
        key = next(iter(self.pr.policy_cache))
        _, value = self.pr.policy_cache[key]
        self.pr.policy_cache[key] = (0.0, value)
        second = self.pr.get_land_use_policies(self.muni, self.prop)
        self.assertIsNot(first, second)

    def test_cache_ttl_constant_is_short(self):
        # Bylaws change frequently; the cache must not be set to days/weeks.
        self.assertLessEqual(CACHE_TTL_SECONDS, 24 * 3600)


class AppErrorSanitizationTest(unittest.TestCase):
    """The analyze endpoint must not echo raw exception text to clients."""

    def test_internal_error_returns_sanitized_message(self):
        from app import app

        # Force an unexpected exception inside the handler.
        with patch(
            "app.property_parser.parse_property_info",
            side_effect=RuntimeError("super secret internal stack info"),
        ):
            client = app.test_client()
            resp = client.post("/api/analyze_property", json={"address": "1 Main St"})

        self.assertEqual(resp.status_code, 500)
        body = resp.get_json()
        self.assertIn("Internal error", body["error"])
        self.assertNotIn("super secret", body["error"])
        self.assertIn("request_id", body)


class HealthEndpointTest(unittest.TestCase):
    def test_health_returns_ok_and_provider_list(self):
        from app import app

        resp = app.test_client().get("/api/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("edmonton", body["providers_registered"])
        self.assertIn("calgary", body["providers_registered"])
        self.assertGreater(body["municipalities"], 0)


class GeocodeBoundaryTests(unittest.TestCase):
    """The boundary check must reject geocodes that landed in a different
    city. This is the failure mode that motivated Option B in the first place."""

    def setUp(self):
        from property_parser import is_point_within_municipality
        self.check = is_point_within_municipality
        self.edmonton = {"name": "Edmonton", "coordinates": {"lat": 53.5444, "lon": -113.4909}}
        self.calgary = {"name": "Calgary", "coordinates": {"lat": 51.0447, "lon": -114.0631}}

    def test_point_in_city_passes(self):
        ok, dist = self.check(53.55, -113.49, self.edmonton)
        self.assertTrue(ok)
        self.assertLess(dist, 5)

    def test_point_in_other_city_rejected(self):
        # Toronto coords against Edmonton — should fail
        ok, dist = self.check(43.6532, -79.3832, self.edmonton)
        self.assertFalse(ok)
        self.assertGreater(dist, 1000)

    def test_calgary_point_rejected_against_edmonton(self):
        ok, dist = self.check(51.0447, -114.0631, self.edmonton)
        self.assertFalse(ok)

    def test_no_centroid_is_permissive(self):
        """If we have no centroid for the municipality, accept the point."""
        ok, dist = self.check(53.5, -113.5, {"name": "Smalltown"})
        self.assertTrue(ok)
        self.assertEqual(dist, 0.0)


class GeocoderFallbackTests(unittest.TestCase):
    """Photon is the primary geocoder; Nominatim is the fallback. When Photon
    fails (timeout / 403 / network), we must transparently fall through to
    Nominatim before giving up."""

    def setUp(self):
        from property_parser import PropertyParser
        self.parser = PropertyParser()

    def test_primary_geocoder_is_photon(self):
        self.assertEqual(self.parser._geocoders[0][0], "photon")
        self.assertEqual(self.parser._geocoders[1][0], "nominatim")

    def test_falls_back_to_nominatim_when_photon_fails(self):
        from geopy.exc import GeocoderServiceError
        from unittest.mock import MagicMock

        photon = MagicMock()
        photon.geocode.side_effect = GeocoderServiceError("403 access denied")
        nominatim = MagicMock()
        nominatim_loc = MagicMock(
            latitude=53.5444, longitude=-113.4909, address="fake address"
        )
        nominatim.geocode.return_value = nominatim_loc
        self.parser._geocoders = [("photon", photon), ("nominatim", nominatim)]

        result = self.parser._geocode_address("1 Main St", "AB")
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "nominatim")
        self.assertAlmostEqual(result["latitude"], 53.5444, places=3)
        photon.geocode.assert_called_once()
        nominatim.geocode.assert_called_once()

    def test_uses_photon_when_it_succeeds(self):
        from unittest.mock import MagicMock

        photon = MagicMock()
        photon_loc = MagicMock(
            latitude=51.0453, longitude=-114.0581, address="Calgary downtown"
        )
        photon.geocode.return_value = photon_loc
        nominatim = MagicMock()
        self.parser._geocoders = [("photon", photon), ("nominatim", nominatim)]

        result = self.parser._geocode_address("downtown Calgary", "AB")
        self.assertEqual(result["source"], "photon")
        # Nominatim must NOT be called when Photon already succeeded
        nominatim.geocode.assert_not_called()

    def test_returns_none_when_all_geocoders_fail(self):
        from geopy.exc import GeocoderTimedOut
        from unittest.mock import MagicMock

        photon = MagicMock()
        photon.geocode.side_effect = GeocoderTimedOut("photon timed out")
        nominatim = MagicMock()
        nominatim.geocode.side_effect = GeocoderTimedOut("nominatim timed out")
        self.parser._geocoders = [("photon", photon), ("nominatim", nominatim)]

        result = self.parser._geocode_address("nowhere real", "")
        self.assertIsNone(result)


class GeocodeBoundaryProviderIntegrationTest(unittest.TestCase):
    """When the geocode lands far from the selected municipality, the provider
    is NOT called at all — we surface outside_coverage immediately."""

    def test_far_point_triggers_outside_coverage_without_calling_provider(self):
        from policy_retrieval import PolicyRetrieval

        pr = PolicyRetrieval()
        muni = {
            "name": "Edmonton",
            "province": "AB",
            "coordinates": {"lat": 53.5444, "lon": -113.4909},
            "land_use_bylaw": "https://www.edmonton.ca",
        }
        # Toronto coordinates — should be rejected before hitting Socrata
        prop = {
            "raw_input": {"address": "weird address"},
            "coordinates": {"latitude": 43.6532, "longitude": -79.3832},
        }
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = AssertionError("provider should not be called")
            policy = pr.get_land_use_policies(muni, prop)
        self.assertEqual(policy["verification_status"], "outside_coverage")
        self.assertIn("km", policy["verification_message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
