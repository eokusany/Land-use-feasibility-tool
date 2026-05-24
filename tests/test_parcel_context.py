"""Tests for the parcel context dataclasses."""

import unittest

from zoning_providers.parcel_context import (
    AdjacentZone,
    AerialImage,
    LotCharacteristics,
    OverlayFlag,
    ParcelContext,
    PermitRecord,
)


class LotCharacteristicsTests(unittest.TestCase):
    def test_to_dict_emits_metric_units(self):
        lot = LotCharacteristics(
            area_m2=465.3,
            frontage_m=12.2,
            depth_m=38.1,
            orientation_deg=92.0,
            source="City of Edmonton Property Information",
            source_url="https://data.edmonton.ca/resource/<id>",
        )
        d = lot.to_dict()
        self.assertEqual(d["area_m2"], 465.3)
        self.assertEqual(d["frontage_m"], 12.2)
        self.assertEqual(d["depth_m"], 38.1)
        self.assertEqual(d["orientation_deg"], 92.0)
        self.assertIn("Edmonton", d["source"])


class AdjacentZoneTests(unittest.TestCase):
    def test_aggregates_count_and_description(self):
        adj = AdjacentZone(code="R-G", name="Residential — Grade-Oriented Infill", count=3)
        d = adj.to_dict()
        self.assertEqual(d["code"], "R-G")
        self.assertEqual(d["count"], 3)


class PermitRecordTests(unittest.TestCase):
    def test_serialises_iso_dates(self):
        p = PermitRecord(
            permit_number="DP-2024-0042",
            issue_date="2024-08-12",
            status="Released",
            work_type="New Building",
            description="Construct a triplex",
            source="City of Edmonton Development Permits",
            source_url="https://data.edmonton.ca/...",
        )
        self.assertEqual(p.to_dict()["issue_date"], "2024-08-12")


class OverlayFlagTests(unittest.TestCase):
    def test_categories_are_explicit(self):
        flag = OverlayFlag(
            category="heritage",
            code="HD-Macdonald",
            description="Designated heritage resource",
            source="City of Edmonton Designated Historic Resources",
            source_url="https://...",
        )
        d = flag.to_dict()
        self.assertEqual(d["category"], "heritage")
        self.assertEqual(d["code"], "HD-Macdonald")

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            OverlayFlag(category="bogus", code="x", description="y",
                        source="s", source_url="u")


class AerialImageTests(unittest.TestCase):
    def test_url_and_attribution_present(self):
        img = AerialImage(
            url="https://api.mapbox.com/styles/v1/...",
            width=600,
            height=400,
            zoom=18,
            attribution="© Mapbox © OpenStreetMap",
        )
        self.assertEqual(img.to_dict()["url"], img.url)
        self.assertIn("Mapbox", img.attribution)


class ParcelContextTests(unittest.TestCase):
    def test_empty_context_serialises_to_nones_and_empty_lists(self):
        ctx = ParcelContext()
        d = ctx.to_dict()
        self.assertIsNone(d["lot"])
        self.assertEqual(d["adjacent_zones"], [])
        self.assertEqual(d["permits"], [])
        self.assertEqual(d["overlay_flags"], [])
        self.assertIsNone(d["aerial_image"])
        self.assertEqual(d["warnings"], [])

    def test_warnings_aggregate(self):
        ctx = ParcelContext()
        ctx.warnings.append("permits API timed out")
        self.assertEqual(ctx.to_dict()["warnings"], ["permits API timed out"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
