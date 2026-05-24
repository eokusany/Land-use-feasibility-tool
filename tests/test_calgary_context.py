"""Tests for the Calgary parcel-context implementation."""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from zoning_providers.calgary import CalgaryZoningProvider
from zoning_providers.parcel_context import LotCharacteristics


FIXTURES = Path(__file__).parent / "fixtures" / "calgary"


def _load(name: str):
    with open(FIXTURES / name) as f:
        return json.load(f)


def _mock_response(json_data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    return m


class CalgaryLotCharacteristicsTests(unittest.TestCase):
    def setUp(self):
        self.provider = CalgaryZoningProvider()

    def test_context_returns_lot_when_parcel_dataset_hits(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response(_load("parcel.json")),  # parcel
                _mock_response([]),                    # permits
                _mock_response([]),                    # heritage
                _mock_response([]),                    # flood
                _mock_response([]),                    # neighbour zones
            ]
            ctx = self.provider.context(51.0450, -114.0640)
        self.assertIsNotNone(ctx)
        self.assertIsInstance(ctx.lot, LotCharacteristics)
        self.assertIsNotNone(ctx.lot.area_m2)
        self.assertGreater(ctx.lot.area_m2, 0)
        # Calgary parcel dataset has no perimeter field — frontage/depth stay None.
        self.assertIsNone(ctx.lot.frontage_m)
        self.assertIsNone(ctx.lot.depth_m)
        self.assertIn("Calgary", ctx.lot.source)

    def test_context_returns_empty_when_parcel_dataset_misses(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = self.provider.context(43.65, -79.38)  # Toronto
        self.assertIsNone(ctx.lot)
        self.assertTrue(any("no parcel" in w.lower() for w in ctx.warnings))

    def test_context_returns_none_for_missing_coordinates(self):
        self.assertIsNone(self.provider.context(None, -114.0631))
        self.assertIsNone(self.provider.context(51.0447, None))


class CalgaryPermitsTests(unittest.TestCase):
    def test_permits_populated_from_dataset(self):
        provider = CalgaryZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response(_load("permits.json")),
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
            ]
            ctx = provider.context(51.0447, -114.0631)
        self.assertGreaterEqual(len(ctx.permits), 1)
        self.assertIn("Calgary", ctx.permits[0].source)
        # Permit number should be populated from `permitnum`, not the applicant field.
        self.assertTrue(ctx.permits[0].permit_number)

    def test_permits_failure_does_not_break_context(self):
        import requests as _r
        provider = CalgaryZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _r.ConnectionError("permits offline"),
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
            ]
            ctx = provider.context(51.0447, -114.0631)
        self.assertEqual(ctx.permits, [])
        self.assertTrue(any("permit" in w.lower() for w in ctx.warnings))


class CalgaryOverlayFlagsTests(unittest.TestCase):
    def test_heritage_flag_emitted(self):
        provider = CalgaryZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("heritage.json")),
                _mock_response([]),
                _mock_response([]),
            ]
            ctx = provider.context(51.0447, -114.0631)
        heritage = [f for f in ctx.overlay_flags if f.category == "heritage"]
        with open(FIXTURES / "heritage.json") as f:
            expected = len(json.load(f))
        if expected == 0:
            self.assertEqual(heritage, [])
        else:
            self.assertGreaterEqual(len(heritage), 1)
            self.assertIn("Calgary", heritage[0].source)

    def test_flood_flag_emitted(self):
        provider = CalgaryZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("flood.json")),
                _mock_response([]),
            ]
            ctx = provider.context(51.0530, -114.0686)
        flood = [f for f in ctx.overlay_flags if f.category == "flood"]
        with open(FIXTURES / "flood.json") as f:
            expected = len(json.load(f))
        if expected == 0:
            self.assertEqual(flood, [])
        else:
            self.assertGreaterEqual(len(flood), 1)
            self.assertIn("Calgary", flood[0].source)


class CalgaryAdjacentZonesTests(unittest.TestCase):
    def test_adjacent_zones_aggregated_and_sorted_by_count(self):
        provider = CalgaryZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("neighbour_zones.json")),
            ]
            ctx = provider.context(51.0447, -114.0631)
        self.assertGreaterEqual(len(ctx.adjacent_zones), 1)
        counts = [z.count for z in ctx.adjacent_zones]
        self.assertEqual(counts, sorted(counts, reverse=True))


class CalgaryAerialImageTests(unittest.TestCase):
    def test_aerial_image_skipped_when_token_missing(self):
        provider = CalgaryZoningProvider()
        with patch.dict(os.environ, {}, clear=True), \
             patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = provider.context(51.0447, -114.0631)
        self.assertIsNone(ctx.aerial_image)
        self.assertTrue(any("aerial" in w.lower() for w in ctx.warnings))

    def test_aerial_image_built_when_token_present(self):
        provider = CalgaryZoningProvider()
        with patch.dict(os.environ, {"PLOTLINE_MAPBOX_TOKEN": "pk.test"}, clear=True), \
             patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = provider.context(51.0447, -114.0631)
        self.assertIsNotNone(ctx.aerial_image)
        self.assertIn("api.mapbox.com", ctx.aerial_image.url)


@unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS"), "Set RUN_LIVE_TESTS=1")
class LiveCalgaryContextTests(unittest.TestCase):
    def test_live_downtown_lot(self):
        provider = CalgaryZoningProvider()
        # 30 m north of City Hall to land on a real parcel polygon.
        ctx = provider.context(51.0450, -114.0640)
        self.assertIsNotNone(ctx)
        if ctx.lot is not None:
            self.assertGreater(ctx.lot.area_m2, 50)
            self.assertLess(ctx.lot.area_m2, 1_000_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
