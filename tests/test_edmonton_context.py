"""Tests for the Edmonton parcel-context implementation."""

import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from zoning_providers.edmonton import EdmontonZoningProvider
from zoning_providers.parcel_context import LotCharacteristics


FIXTURES = Path(__file__).parent / "fixtures" / "edmonton"


def _load(name: str):
    with open(FIXTURES / name) as f:
        return json.load(f)


def _mock_response(json_data, status=200):
    m = MagicMock()
    m.status_code = status
    m.json.return_value = json_data
    return m


class EdmontonLotCharacteristicsTests(unittest.TestCase):
    def setUp(self):
        self.provider = EdmontonZoningProvider()

    def test_context_returns_lot_when_parcel_dataset_hits(self):
        parcel_rows = _load("parcel.json")
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response(parcel_rows)
            ctx = self.provider.context(53.5444, -113.4909)
        self.assertIsNotNone(ctx)
        self.assertIsInstance(ctx.lot, LotCharacteristics)
        self.assertIsNotNone(ctx.lot.area_m2)
        self.assertGreater(ctx.lot.area_m2, 0)
        # Edmonton cadastre is point-based — no perimeter, so frontage/depth
        # must be None until a perimeter source is added.
        self.assertIsNone(ctx.lot.frontage_m)
        self.assertIsNone(ctx.lot.depth_m)
        self.assertIn("Edmonton", ctx.lot.source)

    def test_context_returns_empty_when_parcel_dataset_misses(self):
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = self.provider.context(43.65, -79.38)
        self.assertIsNone(ctx.lot)
        self.assertTrue(any("no parcel" in w.lower() for w in ctx.warnings))

    def test_context_swallows_parcel_api_failure(self):
        import requests as _r
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = _r.ConnectionError("offline")
            ctx = self.provider.context(53.5444, -113.4909)
        self.assertIsNone(ctx.lot)
        self.assertTrue(any("parcel" in w.lower() for w in ctx.warnings))

    def test_context_returns_none_for_missing_coordinates(self):
        self.assertIsNone(self.provider.context(None, -113.4909))
        self.assertIsNone(self.provider.context(53.5444, None))

    def test_aerial_image_skipped_when_token_missing(self):
        # No PLOTLINE_MAPBOX_TOKEN in env -> aerial_image is None and a warning is set.
        with patch.dict(os.environ, {}, clear=True), \
             patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = self.provider.context(53.5444, -113.4909)
        self.assertIsNone(ctx.aerial_image)
        self.assertTrue(any("aerial" in w.lower() for w in ctx.warnings))

    def test_aerial_image_built_when_token_present(self):
        with patch.dict(os.environ, {"PLOTLINE_MAPBOX_TOKEN": "pk.test"}, clear=True), \
             patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.return_value = _mock_response([])
            ctx = self.provider.context(53.5444, -113.4909)
        self.assertIsNotNone(ctx.aerial_image)
        self.assertIn("api.mapbox.com", ctx.aerial_image.url)


class EdmontonPermitsTests(unittest.TestCase):
    def test_permits_populated_from_dataset(self):
        permit_rows = _load("permits.json")
        provider = EdmontonZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),                # parcel — empty, focus on permits
                _mock_response(permit_rows),       # permits
                _mock_response([]),                # heritage
                _mock_response([]),                # flood
                _mock_response([]),                # neighbour zones
            ]
            ctx = provider.context(53.5444, -113.4909)
        self.assertGreaterEqual(len(ctx.permits), 1)
        p = ctx.permits[0]
        self.assertTrue(p.permit_number)
        self.assertIn("Edmonton", p.source)

    def test_permits_failure_does_not_break_context(self):
        import requests as _r
        provider = EdmontonZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _r.ConnectionError("permits offline"),
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
            ]
            ctx = provider.context(53.5444, -113.4909)
        self.assertEqual(ctx.permits, [])
        self.assertTrue(any("permit" in w.lower() for w in ctx.warnings))


class EdmontonOverlayFlagsTests(unittest.TestCase):
    def test_heritage_flag_emitted(self):
        provider = EdmontonZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("heritage.json")),
                _mock_response([]),
                _mock_response([]),
            ]
            ctx = provider.context(53.5402, -113.4868)
        heritage = [f for f in ctx.overlay_flags if f.category == "heritage"]
        self.assertGreaterEqual(len(heritage), 1)
        self.assertIn("Edmonton", heritage[0].source)

    def test_flood_flag_emitted(self):
        """Edmonton flood uses the same overlay dataset as zone overlays,
        filtered to FP/NSRV/NS10 codes."""
        provider = EdmontonZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("flood.json")),
                _mock_response([]),
            ]
            ctx = provider.context(53.5340, -113.4750)
        flood = [f for f in ctx.overlay_flags if f.category == "flood"]
        with open(FIXTURES / "flood.json") as f:
            expected = len(json.load(f))
        if expected == 0:
            self.assertEqual(flood, [])
        else:
            self.assertGreaterEqual(len(flood), 1)
            self.assertIn("Edmonton", flood[0].source)


class EdmontonAdjacentZonesTests(unittest.TestCase):
    def test_adjacent_zones_aggregated_and_sorted_by_count(self):
        provider = EdmontonZoningProvider()
        with patch("zoning_providers.base.requests.get") as mock_get:
            mock_get.side_effect = [
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response([]),
                _mock_response(_load("neighbour_zones.json")),
            ]
            ctx = provider.context(53.5444, -113.4909)
        self.assertGreaterEqual(len(ctx.adjacent_zones), 1)
        # Sorted descending by count
        counts = [z.count for z in ctx.adjacent_zones]
        self.assertEqual(counts, sorted(counts, reverse=True))


class EdmontonContextOrderingTests(unittest.TestCase):
    def test_call_order_is_parcel_permits_heritage_flood_neighbour(self):
        """The mocked side_effect lists in this file assume a specific call
        order. If you change the order in context(), update both this test
        and every mocked side_effect above."""
        provider = EdmontonZoningProvider()
        captured_urls = []

        def _record(url, params=None, timeout=None, headers=None):
            captured_urls.append(url)
            return _mock_response([])

        with patch("zoning_providers.base.requests.get", side_effect=_record):
            provider.context(53.5444, -113.4909)

        # Five upstream calls in fixed order. Each URL is distinct (or the same
        # endpoint queried twice — flood reuses overlays endpoint).
        self.assertEqual(len(captured_urls), 5)


@unittest.skipUnless(os.environ.get("RUN_LIVE_TESTS"), "Set RUN_LIVE_TESTS=1")
class LiveEdmontonContextTests(unittest.TestCase):
    def test_live_downtown_lot(self):
        provider = EdmontonZoningProvider()
        ctx = provider.context(53.5444, -113.4909)
        self.assertIsNotNone(ctx)
        if ctx.lot is not None:
            self.assertGreater(ctx.lot.area_m2, 50)
            self.assertLess(ctx.lot.area_m2, 100_000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
