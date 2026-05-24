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
