"""End-to-end smoke test of the Plotline pipeline (offline).

Exercises property_parser -> municipality_lookup -> policy_retrieval against
the sample cottage-development email referenced in the README. The geocode
call is patched so the test stays hermetic and fast.

Run:
    python -m unittest test_sample_property.py -v
"""

import unittest
from unittest.mock import patch

from municipality_lookup import MunicipalityLookup
from policy_retrieval import PolicyRetrieval
from property_parser import PropertyParser


SAMPLE = {
    "address": "Property north of Black Bull Golf, west of The Village at Pigeon Lake, AB",
    "legal_description": "NE 12-45-26-W4M",
    "additional_info": (
        "14.55 acre rural commercial property directly north of Black Bull Golf "
        "and west of The Village at Pigeon Lake. Plan to develop the north "
        "section with small cottages for rent. The county just installed a "
        "septic lift station to the north. There's no village water — drill wells. "
        "Highway has turning lanes."
    ),
}


class SamplePropertyPipelineTest(unittest.TestCase):
    def setUp(self):
        self.parser = PropertyParser()
        self.lookup = MunicipalityLookup()
        self.policy = PolicyRetrieval()

    def test_pipeline_runs_end_to_end_and_is_honest(self):
        with patch.object(self.parser, "_geocode_address", return_value=None):
            info = self.parser.parse_property_info(
                address=SAMPLE["address"],
                legal_description=SAMPLE["legal_description"],
                additional_info=SAMPLE["additional_info"],
                province="AB",
            )

        self.assertIsNotNone(info, "parser should accept a richly-described rural property")
        self.assertEqual(info["property_details"].get("acreage"), 14.55)
        self.assertIn("rural", info["property_details"].get("zoning_hints", []))
        self.assertIn("commercial", info["property_details"].get("zoning_hints", []))
        self.assertIn("septic", info["property_details"].get("infrastructure_mentions", []))
        # `cottage` (singular) should match thanks to word-boundary regex,
        # even though earlier code only matched the plural.
        intentions = info["property_details"].get("development_intentions", [])
        self.assertTrue("cottage" in intentions or "cottages" in intentions)

        # Municipality lookup: we expect at least *some* candidate to come back
        # via the explicit province + name path, even without coordinates.
        muni = self.lookup.find_by_province_and_city("AB", "Wetaskiwin County") or \
            self.lookup._find_by_name("Wetaskiwin County", "AB")
        self.assertIsNotNone(muni, "Wetaskiwin County should be in the registry")

        policy = self.policy.get_land_use_policies(muni, info)

        # Honest mode: no fabricated zone for a non-Edmonton property.
        self.assertEqual(policy["verification_status"], "unverified")
        self.assertTrue(policy["verification_required"])
        self.assertIsNone(policy["zoning"])
        self.assertEqual(policy["permitted_uses"], [])
        self.assertEqual(policy["setbacks"], {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
